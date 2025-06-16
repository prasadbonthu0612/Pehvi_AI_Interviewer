# Pehvi AI Interviewer

An AI-powered interviewer application that conducts mock interviews using speech recognition and text-to-speech capabilities.

## Features

- Real-time speech recognition using Vosk
- Text-to-speech responses using gTTS
- Interactive chat interface
- Automated feedback generation
- Score assessment based on answer quality

## Setup Instructions

1. Clone the repository:
```bash
git clone <https://github.com/prasadbonthu0612/Pehvi_AI_Interviewer>
cd Pehvi_AI_Interviewer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # On Mac: venv\bin\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download the Vosk model:
- Create a directory: `mkdir vosk-model-small-en-us-0.15`
- Download the model from [Vosk Models](https://alphacephei.com/vosk/models)
- Extract the model files into the `vosk-model-small-en-us-0.15` directory

5. Run the application:
```bash
python main.py
```

## Deployment

This application is configured for deployment on Render. The necessary configuration files (`Procfile` and `requirements.txt`) are included in the repository.

## Environment Variables

The following environment variables need to be set in your deployment environment:

- None required for basic functionality

## License

[Your License Here] 