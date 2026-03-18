from chromadb import PersistentClient

client = PersistentClient(path="chroma_db")

def get_collection(name: str):
    return client.get_or_create_collection(name=name)