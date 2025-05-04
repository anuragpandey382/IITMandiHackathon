def chat():
    """Process chat messages and return AI responses"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Please enter a message."}), 400
        
        logger.info(f"Received message: {user_message[:30]}...")
        
        # Prepare payload for Gemini API
        payload = {
            "contents": [{
                "parts": [{"text": user_message}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        # Call Gemini API
        response = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract response text
        try:
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(f"Generated response: {reply[:30]}...")
            return jsonify({"reply": reply})
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing API response: {e}")
            logger.error(f"Response data: {data}")
            return jsonify({"error": "Error parsing API response"}), 500
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        return jsonify({"error": f"API Error: {str(e)}"}), 502
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500