import matplotlib
matplotlib.use("Agg")  # prevent tkinter/threading crash on Windows
 
from ms_rehab_game.main import main
 
 
if __name__ == "__main__":
    raise SystemExit(main())
 