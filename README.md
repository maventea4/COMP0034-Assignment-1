# README.md

Use README.md to give brief instructions to other developers on what your repo contains and how to use the contents.
Project dirctory is thus shaped: 
COMP0034-Assignment-1/
├── requirements.txt          # Dependencies for the project
├── README.md                 # Project documentation
├── .gitignore                # Git ignore file
├── pyproject.toml            # Project configuration file
├── Data/                     # Data folder
│   ├── london-boroughs_1179.geojson
│   ├── met_police            # Police crime data
├── src/                      # Source code for the Dash app
│   └── app.py                # Main app file for the Dash app
├── tests/                    # Test folder
│   ├── chromedriver          # ChromeDriver executable for Selenium tests
│   └── test_app.py           # Test file containing automated tests
└── .git/                     # Git version control folder

To initialise environment, run:
pip install -r requirements.txt
pip install -e .

To run app, use:
python src/app.py

To run tests, use:
pytest



