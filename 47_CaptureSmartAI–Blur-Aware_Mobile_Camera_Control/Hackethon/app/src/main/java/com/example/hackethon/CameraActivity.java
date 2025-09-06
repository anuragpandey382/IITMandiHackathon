package com.example.hackethon;

import android.Manifest;
import android.content.ContentValues;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.ImageFormat;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.*;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.Image;
import android.media.ImageReader;
import android.media.MediaActionSound;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Log;
import android.util.Size;
import android.view.Surface;
import android.view.TextureView;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import org.opencv.android.OpenCVLoader;
import org.opencv.android.Utils;
import org.opencv.core.CvType;
import org.opencv.core.Core;
import org.opencv.core.Mat;
import org.opencv.core.MatOfDouble;
import org.opencv.imgproc.Imgproc;

import java.io.FileOutputStream;
import java.nio.ByteBuffer;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Date;
import java.util.Locale;

public class CameraActivity extends AppCompatActivity {

    static { if (!OpenCVLoader.initDebug()) Log.e("OpenCV", "OpenCV init failed"); }

    private TextureView textureView;
    private TextView motionText;
    private TextView shutterText;
    private CameraDevice cameraDevice;
    private CameraCaptureSession session;
    private CaptureRequest.Builder previewRequestBuilder;
    private ImageReader captureReader;
    private Size jpegSize;
    private String[] cameraIds;
    private int currentCameraIndex = 0;
    private CameraManager cameraManager;
    private MediaActionSound shutterSound;

    private long exposureUs = 50000000L;
    private int iso = 400;
    private final long MIN_EXP = 1000000L, MAX_EXP = 200000000L;
    private final int MIN_ISO = 100, MAX_ISO = 6400;

    private double avgBlur = 100;
    private double avgBrightness = 100;
    private double avgMotion = 0;

    private static final double TARGET_BRIGHTNESS = 100.0;

    private Mat previousGray;

    @Override
    protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_camera);

        textureView = new TextureView(this);
        ((FrameLayout) findViewById(R.id.camera_container)).addView(textureView, 0);

        motionText = findViewById(R.id.motionParameterText);
        shutterText = findViewById(R.id.shutterSpeedText);
        shutterSound = new MediaActionSound();
        shutterSound.load(MediaActionSound.SHUTTER_CLICK);

        cameraManager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            cameraIds = cameraManager.getCameraIdList();
        } catch (CameraAccessException e) {
            Log.e("CamAct", "Failed to get camera IDs", e);
        }

        findViewById(R.id.captureButton).setOnClickListener(v -> captureImage());
        findViewById(R.id.infoButton).setOnClickListener(v -> toggleInfo());
        findViewById(R.id.toggleButton).setOnClickListener(v -> switchCamera());

        textureView.setSurfaceTextureListener(new TextureView.SurfaceTextureListener() {
            @Override public void onSurfaceTextureAvailable(@NonNull SurfaceTexture st, int w, int h) { openCamera(); }
            @Override public void onSurfaceTextureSizeChanged(@NonNull SurfaceTexture st, int w, int h) {}
            @Override public boolean onSurfaceTextureDestroyed(@NonNull SurfaceTexture st) { return false; }
            @Override public void onSurfaceTextureUpdated(@NonNull SurfaceTexture st) { analyzeFrame(); }
        });
    }

    private void toggleInfo() {
        int current = motionText.getVisibility();
        motionText.setVisibility(current == TextView.VISIBLE ? TextView.GONE : TextView.VISIBLE);
        shutterText.setVisibility(current == TextView.VISIBLE ? TextView.GONE : TextView.VISIBLE);
    }

    private void switchCamera() {
        currentCameraIndex = (currentCameraIndex + 1) % cameraIds.length;
        closeCamera();
        openCamera();
    }

    private void closeCamera() {
        if (session != null) {
            session.close();
            session = null;
        }
        if (cameraDevice != null) {
            cameraDevice.close();
            cameraDevice = null;
        }
        if (captureReader != null) {
            captureReader.close();
            captureReader = null;
        }
    }

    private void openCamera() {
        try {
            String cameraId = cameraIds[currentCameraIndex];
            CameraCharacteristics chars = cameraManager.getCameraCharacteristics(cameraId);
            StreamConfigurationMap map = chars.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
            jpegSize = Arrays.stream(map.getOutputSizes(ImageFormat.JPEG))
                    .max(Comparator.comparingInt(size -> size.getWidth() * size.getHeight()))
                    .orElse(new Size(1920, 1080));

            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.CAMERA}, 100);
                return;
            }

            cameraManager.openCamera(cameraId, new CameraDevice.StateCallback() {
                @Override public void onOpened(@NonNull CameraDevice c) { cameraDevice = c; startPreview(); }
                @Override public void onDisconnected(@NonNull CameraDevice c) { c.close(); }
                @Override public void onError(@NonNull CameraDevice c, int e) { c.close(); }
            }, null);
        } catch (Exception e) {
            Log.e("CamAct", "openCamera", e);
        }
    }

    private void startPreview() {
        try {
            SurfaceTexture tex = textureView.getSurfaceTexture();
            tex.setDefaultBufferSize(1920, 1080);
            Surface surf = new Surface(tex);
            captureReader = ImageReader.newInstance(jpegSize.getWidth(), jpegSize.getHeight(), ImageFormat.JPEG, 1);

            previewRequestBuilder = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
            previewRequestBuilder.addTarget(surf);
            previewRequestBuilder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE);

            cameraDevice.createCaptureSession(Arrays.asList(surf, captureReader.getSurface()),
                    new CameraCaptureSession.StateCallback() {
                        @Override public void onConfigured(@NonNull CameraCaptureSession s) {
                            session = s;
                            try { session.setRepeatingRequest(previewRequestBuilder.build(), null, null); }
                            catch (Exception e) { Log.e("CamAct", "startPreview error", e); }
                        }
                        @Override public void onConfigureFailed(@NonNull CameraCaptureSession s) { Log.e("CamAct", "ConfigFail"); }
                    }, null
            );
        } catch (Exception e) {
            Log.e("CamAct", "startPreview", e);
        }
    }

    private void analyzeFrame() {
        Bitmap bmp = textureView.getBitmap();
        if (bmp == null) return;

        Mat mat = new Mat();
        Utils.bitmapToMat(bmp, mat);
        Imgproc.cvtColor(mat, mat, Imgproc.COLOR_RGBA2GRAY);

        // blur
        Mat lap = new Mat();
        Imgproc.Laplacian(mat, lap, CvType.CV_64F);
        MatOfDouble mean = new MatOfDouble(), std = new MatOfDouble();
        Core.meanStdDev(lap, mean, std);
        double blur = std.get(0, 0)[0];
        lap.release();

        // brightness
        Core.meanStdDev(mat, mean, std);
        double brightness = mean.get(0, 0)[0];

        // motion
        double motion = 0;
        if (previousGray != null) {
            Mat diff = new Mat();
            Core.absdiff(mat, previousGray, diff);
            Imgproc.threshold(diff, diff, 15, 255, Imgproc.THRESH_BINARY);
            motion = Core.countNonZero(diff) * 100.0 / (diff.rows() * diff.cols());
            diff.release();
        }
        if (previousGray != null) previousGray.release();
        previousGray = mat.clone();

        mat.release(); mean.release(); std.release();

        // smoothing
        avgBlur = 0.85 * avgBlur + 0.15 * blur;
        avgBrightness = 0.85 * avgBrightness + 0.15 * brightness;
        avgMotion = 0.85 * avgMotion + 0.15 * motion;

        // ==== Shutter Speed Logic ====
        double motionNorm = Math.max(0, Math.min(1, (avgMotion - 15) / 85.0));
        double minShutter = 1.0 / 1200.0;
        double maxShutter = 1.0 / 200.0;
        double shutterSec = maxShutter * Math.pow(minShutter / maxShutter, motionNorm);
        long newExp = (long)(shutterSec * 1e6);  // in microseconds

        // ==== ISO Calculation ====
        double shutterNorm = Math.min(1.0, shutterSec / (1.0 / 200.0));
        double brightnessNorm = Math.min(1.0, avgBrightness / 160.0);
        double isoPercent = (0.4 + 0.6 * (1.0 - brightnessNorm)) * (0.5 + 0.5 * shutterNorm);
        int newIso = (int)(MIN_ISO + isoPercent * (MAX_ISO - MIN_ISO));

        exposureUs = Math.max(MIN_EXP, Math.min(MAX_EXP, newExp));
        iso = Math.max(MIN_ISO, Math.min(MAX_ISO, newIso));

        final double dispMotion = avgMotion;
        final double dispBlur = avgBlur;
        final double dispBright = avgBrightness;
        final int dispISO = iso;
        final String shutterDisplay = "1/" + (int)(1e6 / exposureUs);

        runOnUiThread(() -> {
            motionText.setText(String.format(Locale.US,
                    "Motion: %.1f%%, Blur: %.1f, Bright: %.1f, ISO: %d",
                    dispMotion, dispBlur, dispBright, dispISO));
            shutterText.setText("Shutter: " + shutterDisplay);
        });
    }

    private void captureImage() {
        try {
            shutterSound.play(MediaActionSound.SHUTTER_CLICK);

            CaptureRequest.Builder cap = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
            cap.addTarget(captureReader.getSurface());
            cap.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_OFF);
            cap.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE);
            cap.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF);
            cap.set(CaptureRequest.SENSOR_EXPOSURE_TIME, exposureUs);
            cap.set(CaptureRequest.SENSOR_SENSITIVITY, iso);
            cap.set(CaptureRequest.JPEG_QUALITY, (byte) 95);

            session.capture(cap.build(), null, null);

            captureReader.setOnImageAvailableListener(reader -> {
                Image img = reader.acquireNextImage();
                new Thread(() -> {
                    saveImage(img);
                    img.close();
                }).start();
            }, null);

        } catch (Exception e) {
            Log.e("CamAct", "capture", e);
        }
    }

    private void saveImage(Image img) {
        ByteBuffer buf = img.getPlanes()[0].getBuffer();
        byte[] data = new byte[buf.remaining()];
        buf.get(data);
        try {
            String ts = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date());
            ContentValues cv = new ContentValues();
            cv.put(MediaStore.Images.Media.DISPLAY_NAME, "IMG_" + ts + ".jpg");
            cv.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
            cv.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/ProSharp");

            Uri u = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, cv);
            try (FileOutputStream fos = (FileOutputStream) getContentResolver().openOutputStream(u)) {
                fos.write(data);
            }
        } catch (Exception e) {
            Log.e("CamAct", "saveImage", e);
        }
    }
}
