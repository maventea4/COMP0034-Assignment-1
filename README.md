# README.md

Use README.md to give brief instructions to other developers on what your repo contains and how to use the contents.
Project dirctory is thus shaped: 
COMP0034-Assignment-1/
├── requirements.txt         
├── README.md                
├── .gitignore               
├── pyproject.toml          
├── Data/                   
│   ├── london-boroughs_1179.geojson
│   ├── crime_cleaned.csv         
├── src/                      
│   └── app.py                
├── tests/                    
│   ├── chromedriver          
│   └── test_app.py          
└── .git/                   

To initialise environment, run:
pip install -r requirements.txt
pip install -e .

To run app, use:
python src/app.py

To run tests, use:
pytest



