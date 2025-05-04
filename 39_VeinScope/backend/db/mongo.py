from pymongo import MongoClient
import gridfs

client = MongoClient("mongodb://localhost:27017/")
db = client["veinscope_db"]
users_collection = db["users"]
fs = gridfs.GridFS(db)
