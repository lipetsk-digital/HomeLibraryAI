# Catalog of the home library with AI-recognition of covers and annotations

[![HomeLibraryAI Avatar](images/avatar_min.jpg)](images/avatar.jpg) ![HomeLibraryAI bot QR-code](images/t_me-home_library_ai_bot.png)


Telegram bot to photo the covers and annotations of your books and create a catalog of your home library. Share the catalog with your friends. No manual input: AI will do everything for you, and it will take no more than 10 seconds to enter one book. If necessary, you can always upload your collection to a file.
https://t.me/home_library_ai_bot

## How it works

![Working environment diagram](images/homelib.drawio.png) 

## GitHub actions secrets

| Name | Description | Usage |
| - | - | - |
| REGISTRY_HOST | Hostname of Container Registry to push docker image | CI/CD |
| REGISTRY_USERNAME | Login of Container Registry | CI/CD |
| REGISTRY_PASSWORD | Password of Container Registry | CI/CD |
| KUBECONFIG | YAML text config of production Kubernates cluster to deploy docker container | CI/CD |
| TELEGRAM_TOKEN | Strint token for production telegram-bot @home_library_ai_bot | Production |

## Project files

- `homelib.py` - core of telegram-bot
- `requirements.txt` - python's library dependencies
- `dockerfile` - instructions: how to build Docker container
- `deployment.yaml` - instructions: how to deploy it on Kubernates cluster
- `.gitignore` - hide my python cache, debug environment variables with sectets, certificates, etc.
- `README.md` - current description
- `\images` - floder with images for current description
- `.github\workflows` - instructions: automatization CI/CD with GitHub Actions

## Basic usage

Just start chatting with [@home_library_ai_bot](https://t.me/home_library_ai_bot) in telegram. We use `Telegram ID` to identificate user and store it's books. Your telegram ID is permanent and does not change when you changing mobile number or telegram nickname.

We store all your photos with unique anonymous identifiers is S3 file storage. So if someone known the photo identificator - they can see it. Access to other people's photos is unlikely, but try not to photograph things that you would not like to allow for public review.

For each book we need two photos:

### 1. Photo of the book cover on plain surface, for example, on the desk. Use the flash to evenly illuminate the book. Avoid mirrored or glass surfaces. 

We use [U-2-Net Salient Object Detection AI-model](https://github.com/xuebinqin/U-2-Net) of th [python rembg library](https://github.com/danielgatis/rembg) to remove background, find the cover's rectanlge and them align it in the form of a vertical rectangle.

| Source photo | Extracted cover |
| - | - |
| [![Example 1 - source](images/th_cover1.jpg)](examples/find_cover/cover1.jpg) | [![Example 1 - result](images/th_output1.jpg)](examples/find_cover/output1.jpg) |
| [![Example 6 - source](images/th_cover6.jpg)](examples/find_cover/cover6.jpg) | [![Example 6 - result](images/th_output6.jpg)](examples/find_cover/output6.jpg) |
