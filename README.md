# PSVSVConvert

## Description
This is the tool for converting **Stardew Valley** proprietary **TBIN** map 
binary format from **PS Vita** specific one to **PC** one and back.

**CPython Interpreter version:** _**3.12+**_ tested. Probably 
**_3.10-3.11_** should work as well.

## Usage

This is the **_console_** utility - so, you should run it from the Terminal.

Utility uses the following syntax to perform any actions:
```bash
py convert.py -Path -Mode
```
Where:
* **_Path_** - path to the file for conversion. If path is incorrect,
  program will suggest select file via **Explorer**.
* **_Mode_** - Can be **_"PSV"_** or **_"PC"_** string in upper or lower case.
  **_PSV_** converts **PC TBIN** file to PS Vita one. **_PC_** converts 
  **PS Vita TBIN** format to **PC** one.
  
  _**If you choose format incorrect, program will raise an exception.**_

As output, program will create **_*.tbinpc_** or **_*.tbinpsv_** file - 
depending on conversion format.

You also can use this to get advice:
```bash
py convert.py -help
```