from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, image_processing, image_fetch  # your routers

app = FastAPI()

origins = [
    "http://localhost:5173", 
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://veinscope.netlify.app/"],     
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(image_processing.router)
app.include_router(image_fetch.router)
