import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictRequest(BaseModel):
    article: str

@app.post("/predict")
async def predict_price(request: PredictRequest):
    model = joblib.load('best.pkl')
    vectorizer = joblib.load('vectorizer.pkl')

    new_text = request.article
    new_text_vectorized = vectorizer.transform([new_text]).toarray()
    probabilities = model.predict_proba(new_text_vectorized)

    predicted_class = probabilities.argmax()
    predicted_probability = probabilities[0][predicted_class]

    if predicted_class == 0:
        prediction_result = "Фейк"
    else:
        prediction_result = "Правда"
    predicted_probability = str(int(float(f"{predicted_probability:.2f}") * 100 ))   
        
    return {"predicted_class": prediction_result, 
            "predicted_probability": predicted_probability
    }

if __name__ == "__main__":
    uvicorn.run(app, port=5000)
