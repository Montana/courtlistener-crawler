# CourtListener (By Thomson Reuters) CLI/GUI Crawler 

Easy search CLI tool for Court Dockets, Cases, and more using the CourtListener API. 

## Usage 

Below an example use case, I ran: 

```python3
python3 courtListener.py "Andrew Weissmann" --court=nysd
```

You can see I searched for cases involving `Andrew Weissmann` and then passed an argument `--court-nysd` this is to define which court the case was filed in. 


![Screenshot 2025-04-16 at 9 57 42 AM](https://github.com/user-attachments/assets/14a77093-8ca1-422e-ad3a-9d63c8ffaf5b)

Here's another example: 

![Screenshot 2025-04-16 at 9 58 39 AM](https://github.com/user-attachments/assets/54b03515-2102-4980-a7df-8518bd06e2c5)

Above you can see I run:

```python3
python3 courtListener.py "Perkins Coie" --court=scotus
```
Which means I'm looking for any filings dealing with Perkins Coie that went to the SCOUTS. 

## GUI 

If you want to use a GUI search you can run: 

```python3
python3 courtListener-gui.py
```
You should then see the GUI pop up: 

<img width="1192" alt="Screenshot 2025-04-17 at 10 11 17 AM" src="https://github.com/user-attachments/assets/9c071dd9-e945-4b77-bfb8-69d0e0d0840f" />

As you can see I searched `Perkins Coie` and I get results all in a easy to use GUI.

## Author

_Michael Mendy_ (c) 2025. 
