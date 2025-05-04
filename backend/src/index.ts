import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { v4 as uuidv4 } from 'uuid';
// Keep this if you *still* need to extract metadata here for some reason,
// otherwise, it might be redundant if Flask handles it.
import * as musicMetadata from 'music-metadata-browser';

// --- Types ---
// Your original response type for the frontend
type AudioUploadResponse = {
  success: boolean;
  message?: string;
  fileName?: string;       // This might now come from Flask
  originalName?: string;
  duration?: number;       // This will likely come from Flask
  duration_formatted?: string; // This will likely come from Flask
  language?: string;       // This will come from Flask
  confidence?: number;     // This will come from Flask
  error?: string;
};

// ADDED: Type for the expected JSON data *from* the Flask backend
// *** Adjust this based on what your Flask app actually returns! ***
type FlaskResponseData = {
  fileName?: string;      // Example field from Flask
  duration?: number;      // Example field from Flask
  language?: string;      // Example field from Flask
  confidence?: number;    // Example field from Flask
  message?: string;       // Optional message from Flask
  // Add any other fields your Flask app returns, e.g., transcription
};
type FlaskLanguageResultData = {
  predicted_language?: string;
  confidence?: number; // Does Flask return confidence on GET too?
  message?: string;    // Optional status/error message from Flask GET
};
const app = new Hono();

const FLASK_BACKEND_URL = 'https://8644-14-139-34-101.ngrok-free.app/predict-language';

// --- CORS Configuration (Your Original) ---
app.use('/*', cors({
  origin: ['http://localhost:5173'],
  allowMethods: ['POST', 'GET', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
  exposeHeaders: ['Content-Type'],
  credentials: true,
  maxAge: 86400
}));

// --- Helper function (Your Original) ---
function formatDuration(seconds: number | undefined): string {
    // Added check for undefined/invalid numbers
    if (typeof seconds !== 'number' || isNaN(seconds) || seconds < 0) {
        return '0:00'; // Or handle as appropriate
    }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// --- Audio upload endpoint - MODIFIED to forward to Flask ---
app.post('/upload-audio-frontend', async (c) => {
  try {
    const form = await c.req.parseBody();
    // Ensure 'file' matches the name attribute of your frontend file input
    const file = form['file'] as File; // Use bracket notation which is safer if name has dashes

    if (!file || !(file instanceof File)) {
      return c.json<AudioUploadResponse>({
        success: false,
        error: 'No audio file provided or invalid file'
      }, 400);
    }

    // Validate audio types (Your Original list - add mp3 if needed)
    const validTypes = ['audio/mpeg', 'audio/webm', 'audio/mp3']; // Explicitly added mp3
    if (!validTypes.includes(file.type)) {
       console.warn(`Received invalid file type: ${file.type}`);
       return c.json<AudioUploadResponse>({
         success: false,
         // Updated error message slightly for clarity
         error: `Only MP3 or WebM audio files are supported. Received type: ${file.type}`
       }, 400);
     }

    // --- START: Forward file to Flask Backend ---
    const formDataToFlask = new FormData();
    // Ensure the field name 'file' matches what your Flask endpoint expects
    formDataToFlask.append('file', file, file.name);

    console.log(`Forwarding file ${file.name} (${file.type}) to Flask: ${FLASK_BACKEND_URL}`);

    const flaskResponse = await fetch(FLASK_BACKEND_URL, {
      method: 'POST',
      body: formDataToFlask,
      // Add headers if Flask requires them (e.g., API keys)
      // headers: { 'Authorization': 'Bearer YOUR_API_KEY' }
    });

    console.log(`Flask response status: ${flaskResponse.status}`);
    // --- END: Forward file to Flask Backend ---


    // --- START: Handle Flask Backend Response ---
    if (!flaskResponse.ok) {
      // Try to get more detailed error from Flask response body
      const errorText = await flaskResponse.text();
      console.error('Flask backend error:', flaskResponse.status, errorText);
      // Return a 502 Bad Gateway error to the original frontend caller
      return c.json<AudioUploadResponse>({
        success: false,
        error: `Flask backend processing failed (${flaskResponse.status}): ${errorText}`
      }, 502);
    }

    // Parse the successful JSON response from Flask
    const flaskResult: FlaskResponseData = await flaskResponse.json();
    console.log('Flask response data:', flaskResult);
    // --- END: Handle Flask Backend Response ---


    // --- START: Construct final response for *your* frontend ---
    // Use data received from Flask, fall back gracefully if needed
    const response: AudioUploadResponse = {
      success: true,
      message: flaskResult.message || 'Audio processed successfully by backend.',
      fileName: flaskResult.fileName || file.name, // Use Flask's filename or original
      originalName: file.name,
      duration: flaskResult.duration, // Use duration from Flask
      duration_formatted: formatDuration(flaskResult.duration), // Format duration from Flask
      language: flaskResult.language || '-', // Use language from Flask
      confidence: flaskResult.confidence // Use confidence from Flask
    };
    // --- END: Construct final response ---


    // *** NOTE: The original metadata extraction and uuid filename generation are removed ***
    // *** as Flask is now assumed to handle this. If you still need the       ***
    // *** music-metadata-browser part, you'd re-insert it before the fetch call. ***


    return c.json(response); // Send the final response back to *your* frontend

  } catch (error) {
    console.error('Error processing upload request:', error); // More specific log message
    return c.json<AudioUploadResponse>({
      success: false,
      // Improved error message for frontend
      error: error instanceof Error ? `Server error: ${error.message}` : 'Failed to process audio file due to an unexpected server error.'
    }, 500);
  }
});

// --- Language detection endpoint (Your Original - Still Mocked) ---
// Consider if this is still needed or how it should get real data
app.get('/get-detected-language', async (c) => {
  try {
    // 1. Get the filename from query parameters (sent by frontend)
    const filename = c.req.query('filename');
    if (!filename) {
      console.warn('/get-detected-language called without filename query parameter.');
      return c.json<AudioUploadResponse>({
        success: false,
        error: 'Missing required query parameter: filename'
      }, 400); // Bad Request
    }

    // 2. Construct the URL for the NEW Flask GET endpoint
    const urlToFlask = new URL(FLASK_BACKEND_URL);
    urlToFlask.searchParams.set('filename', filename); // Add filename=xyz.wav to URL

    console.log(`Workspaceing language result from Flask GET: ${urlToFlask.toString()}`);

    // 3. Fetch the result from Flask's GET endpoint
    const flaskGetResponse = await fetch(urlToFlask.toString(), {
        method: 'GET',
        // Add headers if needed by Flask's GET endpoint
        // headers: { 'Accept': 'application/json' }
    });

    console.log(`Flask GET response status: ${flaskGetResponse.status}`);

    // 4. Handle Flask GET response
    if (!flaskGetResponse.ok) {
        const errorText = await flaskGetResponse.text();
        console.error('Flask GET backend error:', flaskGetResponse.status, errorText);
        return c.json<AudioUploadResponse>({
            success: false,
            error: `Flask backend failed to get language result (${flaskGetResponse.status}): ${errorText}`
        }, 502); // Bad Gateway or appropriate error
    }

    // 5. Parse the JSON response from Flask's GET endpoint
    const flaskResult: FlaskLanguageResultData = await flaskGetResponse.json();
    console.log('Flask GET response data:', flaskResult);

    // 6. Construct the response for Hono frontend
    //    Focus on returning the language data fetched.
    const response: AudioUploadResponse = {
        success: true,
        message: flaskResult.message || `Language result fetched successfully for ${filename}`,
        language: flaskResult.predicted_language || '-', // Language from Flask GET response
        confidence: flaskResult.confidence, // Confidence from Flask GET response (if provided)
        // Include other fields only if relevant and returned by Flask GET
        fileName: filename // Echo back the requested filename
    };

    return c.json(response);

  } catch (error) {
    console.error('Error in /get-detected-language:', error);
    return c.json<AudioUploadResponse>({
      success: false,
      error: error instanceof Error ? `Server error: ${error.message}` : 'Failed to process get-detected-language request.'
    }, 500);
  }
});
export default app;