import { v4 as uuidv4 } from "uuid";
import { Message } from "@/types/chat";

interface ChatResponse {
  message: string;
  sessionId: string;
  reference_links?: string[];
  relevant_docs?: any[];
}

class ChatService {
  private sessionId: string | null = null;
  private apiUrl =
    "https://421d-2409-40d7-e8-dce-4026-1aab-2ef2-879d.ngrok-free.app/chat/form";

  constructor() {
    // Only access localStorage in browser environment
    if (typeof window !== 'undefined') {
      // Try to load session ID from localStorage
      this.sessionId = localStorage.getItem("chatSessionId");
      if (!this.sessionId) {
        this.sessionId = this.generateSessionId();
        localStorage.setItem("chatSessionId", this.sessionId);
      }
    }
  }

  private generateSessionId(): string {
    return uuidv4();
  }

  public getSessionId(): string {
    // Initialize sessionId if it hasn't been set yet (e.g., in SSR context)
    if (!this.sessionId) {
      this.sessionId = this.generateSessionId();
      // Save to localStorage if in browser
      if (typeof window !== 'undefined') {
        localStorage.setItem("chatSessionId", this.sessionId);
      }
    }
    return this.sessionId;
  }

  public resetSession(): void {
    this.sessionId = this.generateSessionId();
    if (typeof window !== 'undefined') {
      localStorage.setItem("chatSessionId", this.sessionId);
    }
  }

  // Rest of the service remains unchanged...
  public async sendMessage(
    message: string,
    image?: File
  ): Promise<ChatResponse> {
    const formData = new FormData();

    // Add the text message
    formData.append("prompt", message);

    // Add the session ID
    formData.append("sessionid", this.getSessionId());

    // Add image if provided
    if (image) {
      formData.append("image", image);
    }

    try {
      console.log("Sending request to:", this.apiUrl);

      const response = await fetch(this.apiUrl, {
        method: "POST",
        body: formData,
        // No Content-Type header - fetch API sets it automatically with boundary
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = await response.json();
      console.log("Response from server:", data);
      
      return {
        message: data.final_response || data.response || data.message || "No response from server",
        sessionId: this.sessionId as string,
        reference_links: data.reference_links || [],
        relevant_docs: data.relevant_docs || []
      };
    } catch (error) {
      console.error("Error sending message:", error);
      throw error;
    }
  }
}

// Create a singleton instance to be used throughout the app
export const chatService = new ChatService();