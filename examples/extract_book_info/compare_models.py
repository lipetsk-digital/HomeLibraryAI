#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import asyncio
import aiohttp
import base64
import re
import time
from pathlib import Path
import configparser
import pandas as pd
from io import StringIO
from openai import AsyncOpenAI
import openpyxl
from openpyxl.styles import Alignment, Font

# Getting the directory where the script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Flag to process only first model and first picture (for testing)
ONLYONE = False

# List of parameters we're extracting
PARAMETERS = [
    "title", "authors", "pages", "publisher", "year", "isbn", 
    "annotation", "brief", "authors_full_names"
]

# Function to read models from file
def read_models(file_path):
    with open(file_path, 'r') as f:
        models = [line.strip() for line in f if line.strip()]
        models.sort()  # Sort models alphabetically
        return models

# Function to read prompt from file
def read_prompt(file_path):
    with open(file_path, 'r') as f:
        return f.read().strip()

# Function to encode image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to clean response text
def clean_response(text):
    # Remove code block markers
    text = re.sub(r'```(?:ini)?', '', text)
    
    # Filter out lines without equals sign
    lines = []
    for line in text.splitlines():
        # Keep section headers and lines with equals sign
        if line.strip().startswith('[') or '=' in line:
            lines.append(line)
    
    # Ensure we have a section header
    if not any(line.strip().startswith('[') for line in lines):
        lines.insert(0, "[book]")
    
    return '\n'.join(lines)

# Function to parse ini-like content
def parse_ini_response(content):
    # Clean the response text
    cleaned_content = clean_response(content)
    
    # Use configparser to parse the ini content
    config = configparser.ConfigParser()
    try:
        config.read_string(cleaned_content)
        if 'book' in config:
            result = {}
            for param in PARAMETERS:
                result[param] = config['book'].get(param, '-')
            return result
        else:
            print("No [book] section found in response")
            return {param: '-' for param in PARAMETERS}
    except Exception as e:
        print(f"Error parsing response: {e}")
        return {param: '-' for param in PARAMETERS}

# Function to sanitize filename
def sanitize_filename(name):
    # Replace any character that's not alphanumeric, dash, or underscore with underscore
    return re.sub(r'[^\w\-]', '_', name)

# Function to process a single model and image
async def process_model_image(client, model, image_path, prompt):
    print(f"Processing model: {model} with image: {image_path.name}")
    
    try:
        start_time = time.time()
        image_base64 = encode_image(image_path)
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]}
            ],
            max_tokens=4000
        )
        
        # Calculate time taken in seconds
        elapsed_time = time.time() - start_time
        
        response_text = response.choices[0].message.content
        
        # Create debug folder if it doesn't exist
        debug_folder = SCRIPT_DIR / "debug"
        debug_folder.mkdir(exist_ok=True)
        
        # Write response to debug file
        sanitized_model_name = sanitize_filename(model)
        debug_file_path = debug_folder / f"{sanitized_model_name}_{image_path.stem}.txt"
        with open(debug_file_path, 'w', encoding='utf-8') as f:
            f.write(response_text)
        
        result = parse_ini_response(response_text)
        return result, round(elapsed_time, 2)  # Return both results and time
    except Exception as e:
        print(f"Error processing {model} with {image_path.name}: {e}")
        
        # Calculate elapsed time even on error
        elapsed_time = time.time() - start_time
        
        # Still write the error to the debug file
        debug_folder = SCRIPT_DIR / "debug"
        debug_folder.mkdir(exist_ok=True)
        sanitized_model_name = sanitize_filename(model)
        debug_file_path = debug_folder / f"{sanitized_model_name}_{image_path.stem}.txt"
        with open(debug_file_path, 'w', encoding='utf-8') as f:
            f.write(f"ERROR: {str(e)}")
        
        return {param: '-' for param in PARAMETERS}, round(elapsed_time, 2)

# Main function
async def main():
    # 1. Read environment variables
    gpt_url = os.environ.get('GPT_URL')
    gpt_api_token = os.environ.get('GPT_API_TOKEN')
    gpt_model = os.environ.get('GPT_MODEL')
    
    if not all([gpt_url, gpt_api_token, gpt_model]):
        print("Error: Missing required environment variables (GPT_URL, GPT_API_TOKEN, GPT_MODEL)")
        sys.exit(1)
    
    # 2. Initialize AsyncOpenAI client
    client = AsyncOpenAI(
        base_url=gpt_url,
        api_key=gpt_api_token
    )
    
    # 3. Read models list
    models_path = SCRIPT_DIR / "models.txt"
    models = read_models(models_path)
    print(f"Found {len(models)} models: {', '.join(models)}")
    
    # 4. Read prompt
    prompt_path = SCRIPT_DIR / "prompt.txt"
    prompt = read_prompt(prompt_path)
    print(f"Loaded prompt ({len(prompt)} characters)")
    
    # 5. Find all JPG images in the script directory
    images = list(SCRIPT_DIR.glob("*.jpg"))
    images.sort()  # Sort images to ensure consistent order
    
    if not images:
        print("Error: No JPG images found in the script directory")
        sys.exit(1)
    
    print(f"Found {len(images)} images: {', '.join(img.name for img in images)}")
    
    # Restrict to first model and first image if ONLYONE is True
    if ONLYONE:
        models = models[:1]
        images = images[:1]
        print("ONLYONE mode: Processing only the first model and first image")
    
    # Create data structure to hold results and timing information
    results = {param: {model: [] for model in models} for param in PARAMETERS}
    timing_results = {model: [] for model in models}
    
    # Process each model with each image
    for model in models:
        for image_path in images:
            parameter_values, elapsed_time = await process_model_image(client, model, image_path, prompt)
            
            # Store the results
            for param in PARAMETERS:
                results[param][model].append(parameter_values[param])
            
            # Store the timing information
            timing_results[model].append(elapsed_time)
            print(f"Completed {model} with {image_path.name} in {elapsed_time} seconds")
    
    # 7. Create excel file
    excel_path = SCRIPT_DIR / "model_comparison_results.xlsx"
    print(f"Creating Excel report at {excel_path}")
    
    # Create a Pandas Excel writer using openpyxl as the engine
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # First, write the timing information to a sheet
        df_timing = pd.DataFrame({
            f"{image_path.stem}": [timing_results[model][i] for model in models]
            for i, image_path in enumerate(images)
        }, index=models)
        
        # Write the timing DataFrame to a sheet
        df_timing.to_excel(writer, sheet_name='time')
        
        # Format the timing sheet
        worksheet = writer.sheets['time']
        worksheet.column_dimensions['A'].width = 40  # Models column
        for i, col in enumerate(['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'], 1):
            if i <= len(images) + 1:
                worksheet.column_dimensions[col].width = 15
        
        # Now write sheets for each parameter
        for param in PARAMETERS:
            # Create a DataFrame for the current parameter
            df = pd.DataFrame({
                f"{image_path.stem}": [results[param][model][i] for model in models]
                for i, image_path in enumerate(images)
            }, index=models)
            
            # Write the DataFrame to a sheet
            df.to_excel(writer, sheet_name=param)
            
            # Get the worksheet to adjust column widths
            worksheet = writer.sheets[param]
            
            # Adjust column widths (header and first column)
            worksheet.column_dimensions['A'].width = 40  # Models column
            
            # Adjust other columns width
            for i, col in enumerate(['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'], 1):  # Columns for images
                if i <= len(images) + 1:  # +1 for the index column
                    worksheet.column_dimensions[col].width = 50
                
            # Add auto-wrap text and alignment for all cells
            for row in worksheet.iter_rows():
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True, vertical='top')
    
    print(f"Results saved to {excel_path}")

if __name__ == "__main__":
    asyncio.run(main())