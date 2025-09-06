package com.example.hackethon;

import android.Manifest;
import android.content.ContentValues;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.ImageFormat;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.*;
import android.media.Image;
import android.media.ImageReader;
import android.media.MediaActionSound;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Log;
import android.view.Surface;
import android.view.TextureView;
import android.widget.ImageView;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import java.io.FileOutputStream;
import java.nio.ByteBuffer;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Date;
import java.util.Locale;

public class NormalCameraActivity extends AppCompatActivity {

    private TextureView textureView;
    private ImageView btnCapture, toggleButton;
    private CameraDevice cameraDevice;
    private CameraCaptureSession session;
    private ImageReader imageReader;
    private CaptureRequest.Builder previewRequestBuilder;
    private MediaActionSound shutterSound = new MediaActionSound();

    private boolean isUsingFrontCamera = false;
    private String currentCameraId = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_normal_camera);

        textureView = findViewById(R.id.textureView);
        btnCapture = findViewById(R.id.btnCapture);
        toggleButton = findViewById(R.id.toggleButton);

        textureView.setSurfaceTextureListener(textureListener);
        btnCapture.setOnClickListener(v -> captureImage());
        toggleButton.setOnClickListener(v -> toggleCamera());
    }

    private final TextureView.SurfaceTextureListener textureListener = new TextureView.SurfaceTextureListener() {
        @Override
        public void onSurfaceTextureAvailable(@NonNull SurfaceTexture surface, int width, int height) {
            openCamera();
        }

        @Override public void onSurfaceTextureSizeChanged(@NonNull SurfaceTexture surface, int width, int height) {}
        @Override public boolean onSurfaceTextureDestroyed(@NonNull SurfaceTexture surface) { return false; }
        @Override public void onSurfaceTextureUpdated(@NonNull SurfaceTexture surface) {}
    };

    private void openCamera() {
        shutterSound.load(MediaActionSound.SHUTTER_CLICK);

        CameraManager mgr = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            currentCameraId = getCameraId(isUsingFrontCamera);
            if (currentCameraId == null) {
                Log.e("Camera", "No suitable camera found.");
                return;
            }

            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.CAMERA}, 101);
                return;
            }

            mgr.openCamera(currentCameraId, new CameraDevice.StateCallback() {
                @Override
                public void onOpened(@NonNull CameraDevice c) {
                    cameraDevice = c;
                    startPreview();
                }

                @Override public void onDisconnected(@NonNull CameraDevice c) { c.close(); }
                @Override public void onError(@NonNull CameraDevice c, int error) { c.close(); }
            }, null);
        } catch (Exception e) {
            Log.e("Camera", "openCamera", e);
        }
    }

    private String getCameraId(boolean useFront) {
        try {
            CameraManager mgr = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
            for (String id : mgr.getCameraIdList()) {
                CameraCharacteristics chars = mgr.getCameraCharacteristics(id);
                Integer facing = chars.get(CameraCharacteristics.LENS_FACING);
                if (useFront && facing == CameraCharacteristics.LENS_FACING_FRONT) return id;
                if (!useFront && facing == CameraCharacteristics.LENS_FACING_BACK) return id;
            }
        } catch (Exception e) {
            Log.e("Camera", "getCameraId", e);
        }
        return null;
    }

    private void toggleCamera() {
        isUsingFrontCamera = !isUsingFrontCamera;
        if (session != null) session.close();
        if (cameraDevice != null) cameraDevice.close();
        openCamera();
    }

    private void startPreview() {
        try {
            SurfaceTexture texture = textureView.getSurfaceTexture();
            texture.setDefaultBufferSize(1920, 1080);
            Surface previewSurface = new Surface(texture);

            imageReader = ImageReader.newInstance(1920, 1080, ImageFormat.JPEG, 1);
            imageReader.setOnImageAvailableListener(reader -> {
                Image image = reader.acquireNextImage();
                ByteBuffer buffer = image.getPlanes()[0].getBuffer();
                byte[] bytes = new byte[buffer.remaining()];
                buffer.get(bytes);
                saveImage(bytes);
                image.close();
            }, null);

            previewRequestBuilder = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
            previewRequestBuilder.addTarget(previewSurface);

            cameraDevice.createCaptureSession(Arrays.asList(previewSurface, imageReader.getSurface()),
                    new CameraCaptureSession.StateCallback() {
                        @Override public void onConfigured(@NonNull CameraCaptureSession s) {
                            session = s;
                            try {
                                session.setRepeatingRequest(previewRequestBuilder.build(), null, null);
                            } catch (Exception e) {
                                Log.e("Camera", "startPreview", e);
                            }
                        }

                        @Override public void onConfigureFailed(@NonNull CameraCaptureSession s) {
                            Log.e("Camera", "Config failed");
                        }
                    }, null);
        } catch (Exception e) {
            Log.e("Camera", "startPreview error", e);
        }
    }

    private void captureImage() {
        try {
            if (cameraDevice == null || imageReader == null) {
                Log.e("Camera", "Device/ImageReader not ready");
                return;
            }

            shutterSound.play(MediaActionSound.SHUTTER_CLICK);

            CaptureRequest.Builder captureRequest = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
            captureRequest.addTarget(imageReader.getSurface());
            captureRequest.set(CaptureRequest.CONTROL_MODE, CameraMetadata.CONTROL_MODE_AUTO);

            session.capture(captureRequest.build(), new CameraCaptureSession.CaptureCallback() {
                @Override
                public void onCaptureCompleted(@NonNull CameraCaptureSession session,
                                               @NonNull CaptureRequest request,
                                               @NonNull TotalCaptureResult result) {
                    super.onCaptureCompleted(session, request, result);
                    Log.d("Camera", "Image captured");
                }
            }, null);
        } catch (Exception e) {
            Log.e("Camera", "captureImage error", e);
        }
    }

    private void saveImage(byte[] data) {
        try {
            String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date());
            ContentValues values = new ContentValues();
            values.put(MediaStore.Images.Media.DISPLAY_NAME, "IMG_" + timeStamp + ".jpg");
            values.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
            values.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/Camera2");

            Uri uri = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
            if (uri != null) {
                try (FileOutputStream out = (FileOutputStream) getContentResolver().openOutputStream(uri)) {
                    out.write(data);
                }
            }
        } catch (Exception e) {
            Log.e("Camera", "saveImage", e);
        }
    }
}
