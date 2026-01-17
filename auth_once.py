from upload import get_youtube_service

print("Starting one-time YouTube authentication...")
youtube = get_youtube_service()
print("✅ Authentication successful. token.pickle created.")