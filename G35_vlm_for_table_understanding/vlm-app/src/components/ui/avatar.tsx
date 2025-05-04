"use client"

import React from "react"
import Image from "next/image"
import { cn } from "@/lib/utils"

interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string
  alt?: string
  fallback?: string
  size?: number
}

export const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, src, alt = "", fallback, size = 40, ...props }, ref) => {
    const [hasError, setHasError] = React.useState(false)

    return (
      <div
        ref={ref}
        className={cn("relative flex shrink-0 overflow-hidden rounded-full", className)}
        style={{ width: size, height: size }}
        {...props}
      >
        {src && !hasError ? (
          <div className="relative h-full w-full">
            <Image
              src={src || "/placeholder.svg"}
              alt={alt}
              fill
              className="object-cover"
              onError={() => setHasError(true)}
            />
          </div>
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-muted text-muted-foreground">
            {fallback ? (
              <span className="text-sm font-medium">{fallback}</span>
            ) : (
              <span className="text-sm font-medium">{alt.charAt(0)?.toUpperCase() || "U"}</span>
            )}
          </div>
        )}
      </div>
    )
  },
)

Avatar.displayName = "Avatar"
