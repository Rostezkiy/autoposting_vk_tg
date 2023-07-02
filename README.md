# autoposting_vk_tg
Simple application for autoposting from VK group to Telegram channel. 
Works with closed groups/channels. 
Using long polling. 
Configuration files for all needed tokens, variables, logging.
Logging into file and log rotation. (log example added)


_Preparation:_

- Open config.ini and check what information you need to get.
- Create telegram bot and add it at your channel with admin rights.
- Obtain VK token, it must be user access token, with "wall, groups" privileges.
- Fill in **config.ini** correctly. 
  
_Start:_ 

- pip install -r requirements.txt
- python main.py
- enjoy

**In case of errors - please, report bugs at 'Issues'. Thank you.**
