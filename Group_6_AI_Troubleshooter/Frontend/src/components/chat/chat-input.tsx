'use client';

import { useState, useRef, FormEvent, ChangeEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { PaperclipIcon, SendIcon, XIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSendMessage: (message: string, image?: File) => void;
  isLoading?: boolean;
  onFocusChange?: (focused: boolean) => void;
}

export function ChatInput({ onSendMessage, isLoading = false, onFocusChange }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() || imageFile) {
      onSendMessage(message, imageFile || undefined);
      setMessage('');
      setImageFile(null);
      setImagePreview(null);
    }
  };

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      setImageFile(file);
      
      // Create image preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveImage = () => {
    setImageFile(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFocus = () => {
    onFocusChange?.(true);
  };

  const handleBlur = () => {
    // Only report not focused if the text field is empty
    if (!message.trim()) {
      onFocusChange?.(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t flex flex-col">
      {/* Image preview */}
      {imagePreview && (
        <div className="relative mb-2 inline-block">
          <img 
            src={imagePreview} 
            alt="Upload preview" 
            className="max-h-32 rounded-md"
          />
          <Button
            type="button"
            variant="destructive"
            size="icon"
            className="absolute top-1 right-1 h-6 w-6 rounded-full"
            onClick={handleRemoveImage}
          >
            <XIcon className="h-3 w-3" />
          </Button>
        </div>
      )}
      
      <div className="flex items-end gap-2">
        <div className="relative flex-1">
          <Textarea
            placeholder="Type your message..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="min-h-[50px] resize-none pr-12"
            onFocus={handleFocus}
            onBlur={handleBlur}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <div className="absolute bottom-2 right-2 flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground"
              onClick={() => fileInputRef.current?.click()}
            >
              <PaperclipIcon className="h-4 w-4" />
              <span className="sr-only">Attach image</span>
            </Button>
            <input
              type="file"
              ref={fileInputRef}
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        </div>
        <Button 
          type="submit" 
          size="icon" 
          disabled={isLoading || (!message.trim() && !imageFile)}
          className={cn(
            "h-10 w-10",
            isLoading && "animate-pulse",
          )}
        >
          <SendIcon className="h-4 w-4 text-2xl" />
          <span className="sr-only">Send</span>
        </Button>
      </div>
    </form>
  );
}