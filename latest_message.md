That ran very quickly on my end. Hopefully, the timing data you captured on your side looks good!

Just a quick reminder: I see line 45 is still pointing to the old location:
```python
AI_START_DIR = r"D:\GoogleDrive\Core\Cortana"
```
If you update that to `r"D:\CAS"`, you won't have to keep running the `cd` command every time you restart the program.

Did that capture the timing metrics you needed?