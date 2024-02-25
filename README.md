An RNG Timer specifically designed for Generation 3 Pokémon games. 
It aids players in precisely timing their actions to manipulate the game's RNG for desired outcomes.

![programme](https://github.com/T0T0W/G3-Sniper/assets/161255413/28d979c8-966c-4ccb-b19e-cbe03c087f95)

![NOICE](https://github.com/T0T0W/G3-Sniper/assets/161255413/9b91a6b9-ddc2-4e72-93a9-5941b88921aa)



The script is compiled into a .exe file using Pyinstaller. Windows Defender will think the file is unsafe. It's a false positive.

If you want to use the python script directly:

Create a folder which include the following files:
- G3_Sniper.exe
- icon.png
- logo.png

And simply run the .py file :D

If you want to compile it yourself using pyinstaller:

Create a folder which include the following files:
- G3_Sniper.exe
- icon.png
- logo.png
- icon.ico

Open CMD into the folder and run this command:

pyinstaller -w --onefile --icon=icon.ico --add-data "logo.png;." --add-data "icon.png;." G3_Sniper.py
