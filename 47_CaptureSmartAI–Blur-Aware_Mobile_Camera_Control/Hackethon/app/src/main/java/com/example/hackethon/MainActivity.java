//package com.example.hackethon;
//
//import android.Manifest;
//import android.content.ContentValues;
//import android.content.Context;
//import android.content.pm.PackageManager;
//import android.graphics.Bitmap;
//import android.graphics.BitmapFactory;
//import android.graphics.ImageFormat;
//import android.graphics.SurfaceTexture;
//import android.hardware.camera2.*;
//import android.media.Image;
//import android.media.ImageReader;
//import android.net.Uri;
//import android.os.Bundle;
//import android.os.Environment;
//import android.provider.MediaStore;
//import android.util.Log;
//import android.view.Surface;
//import android.view.TextureView;
//import android.widget.FrameLayout;
//import android.widget.ImageView;
//import android.widget.TextView;
//
//import androidx.annotation.NonNull;
//import androidx.appcompat.app.AppCompatActivity;
//import androidx.core.app.ActivityCompat;
//
//import org.opencv.android.OpenCVLoader;
//import org.opencv.android.Utils;
//import org.opencv.core.CvType;
//import org.opencv.core.Core;
//import org.opencv.core.Mat;
//import org.opencv.core.MatOfDouble;
//import org.opencv.imgproc.Imgproc;
//
//import java.io.ByteArrayOutputStream;
//import java.io.FileOutputStream;
//import java.nio.ByteBuffer;
//import java.text.SimpleDateFormat;
//import java.util.Date;
//import java.util.Locale;
//
//public class MainActivity extends AppCompatActivity {
//    static { if (!OpenCVLoader.initDebug()) Log.e("OpenCV", "Init failed"); }
//
//    private TextureView textureView;
//    private TextView motionParameterText, shutterSpeedText;
//    private boolean isInfoVisible = false;
//
//    private CameraDevice cameraDevice;
//    private CameraCaptureSession session;
//    private CaptureRequest.Builder previewRequestBuilder;
//    private ImageReader captureReader;
//
//    private boolean isUsingFrontCamera = false;
//    private String currentCameraId = null;
//
//    private long recommendedExposureUs = 50000000L;
//    private final long MIN_EXP = 1000000L, MAX_EXP = 200000000L;
//    private int recommendedIso = 400;
//    private final int MAX_ISO = 3200;
//
//    private static final double TARGET_LAPLACIAN_VAR = 100.0;
//    private static final double TARGET_BRIGHTNESS = 100.0;
//    private static final double MOTION_THRESHOLD_PERCENT = 5.0;
//
//    private Mat previousGray;
//
//    @Override
//    protected void onCreate(Bundle s) {
//        super.onCreate(s);
//        setContentView(R.layout.activity_camera);
//
//        textureView = new TextureView(this);
//        ((FrameLayout)findViewById(R.id.camera_container)).addView(textureView, 0);
//
//        motionParameterText = findViewById(R.id.motionParameterText);
//        shutterSpeedText = findViewById(R.id.shutterSpeedText);
//
//        motionParameterText.setVisibility(TextView.GONE);
//        shutterSpeedText.setVisibility(TextView.GONE);
//
//        findViewById(R.id.captureButton).setOnClickListener(v -> captureImage());
//        findViewById(R.id.toggleButton).setOnClickListener(v -> toggleCamera());
//        findViewById(R.id.infoButton).setOnClickListener(v -> toggleInfo());
//
//        textureView.setSurfaceTextureListener(new TextureView.SurfaceTextureListener() {
//            @Override public void onSurfaceTextureAvailable(@NonNull SurfaceTexture st, int w, int h) { openCamera(); }
//            @Override public void onSurfaceTextureSizeChanged(@NonNull SurfaceTexture st, int w, int h) {}
//            @Override public boolean onSurfaceTextureDestroyed(@NonNull SurfaceTexture st) { return false; }
//            @Override public void onSurfaceTextureUpdated(@NonNull SurfaceTexture st) { analyzeFrame(); }
//        });
//    }
//
//    private void toggleInfo() {
//        isInfoVisible = !isInfoVisible;
//        int visibility = isInfoVisible ? TextView.VISIBLE : TextView.GONE;
//        float targetAlpha = isInfoVisible ? 1f : 0f;
//        motionParameterText.setVisibility(visibility);
//        shutterSpeedText.setVisibility(visibility);
//
//
//        animateVisibility(motionParameterText, visibility, targetAlpha);
//        animateVisibility(shutterSpeedText, visibility, targetAlpha);
//    }
//
//    private void animateVisibility(TextView view, int visibility, float targetAlpha) {
//        view.animate()
//                .alpha(targetAlpha)
//                .setDuration(300)
//                .withStartAction(() -> {
//                    if (visibility == TextView.VISIBLE) view.setVisibility(TextView.VISIBLE);
//                })
//                .withEndAction(() -> {
//                    if (visibility == TextView.GONE) view.setVisibility(TextView.GONE);
//                })
//                .start();
//    }
//
//
//    private void openCamera() {
//        CameraManager mgr = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
//        try {
//            String id = getCameraId(isUsingFrontCamera);
//            currentCameraId = id;
//
//            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
//                ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.CAMERA}, 100);
//                return;
//            }
//
//            mgr.openCamera(id, new CameraDevice.StateCallback() {
//                @Override public void onOpened(@NonNull CameraDevice c) {
//                    cameraDevice = c;
//                    startPreview();
//                }
//                @Override public void onDisconnected(@NonNull CameraDevice c) { c.close(); }
//                @Override public void onError(@NonNull CameraDevice c, int e) { c.close(); }
//            }, null);
//        } catch (Exception e) {
//            Log.e("CamAct", "openCamera", e);
//        }
//    }
//
//    private String getCameraId(boolean useFront) {
//        try {
//            CameraManager mgr = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
//            for (String id : mgr.getCameraIdList()) {
//                CameraCharacteristics chars = mgr.getCameraCharacteristics(id);
//                Integer facing = chars.get(CameraCharacteristics.LENS_FACING);
//                if (useFront && facing == CameraCharacteristics.LENS_FACING_FRONT) return id;
//                if (!useFront && facing == CameraCharacteristics.LENS_FACING_BACK) return id;
//            }
//        } catch (Exception e) {
//            Log.e("CamAct", "getCameraId", e);
//        }
//        return null;
//    }
//
//    private void toggleCamera() {
//        isUsingFrontCamera = !isUsingFrontCamera;
//        if (session != null) session.close();
//        if (cameraDevice != null) cameraDevice.close();
//        openCamera();
//    }
//
//    private void startPreview() {
//        try {
//            SurfaceTexture tex = textureView.getSurfaceTexture();
//            tex.setDefaultBufferSize(1920, 1080);
//            Surface surf = new Surface(tex);
//            captureReader = ImageReader.newInstance(1920, 1080, ImageFormat.JPEG, 1);
//
//            previewRequestBuilder = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
//            previewRequestBuilder.addTarget(surf);
//            previewRequestBuilder.set(CaptureRequest.CONTROL_MODE, CameraMetadata.CONTROL_MODE_AUTO);
//            previewRequestBuilder.set(CaptureRequest.CONTROL_AE_MODE, CameraMetadata.CONTROL_AE_MODE_ON);
//
//            cameraDevice.createCaptureSession(
//                    java.util.Arrays.asList(surf, captureReader.getSurface()),
//                    new CameraCaptureSession.StateCallback() {
//                        @Override public void onConfigured(@NonNull CameraCaptureSession s) {
//                            session = s;
//                            try {
//                                session.setRepeatingRequest(previewRequestBuilder.build(), null, null);
//                            } catch (Exception e) { Log.e("CamAct", "startPreview error", e); }
//                        }
//                        @Override public void onConfigureFailed(@NonNull CameraCaptureSession s) {
//                            Log.e("CamAct", "ConfigFail");
//                        }
//                    }, null
//            );
//        } catch (Exception e) {
//            Log.e("CamAct", "startPreview", e);
//        }
//    }
//
//    private void analyzeFrame() {
//        Bitmap bmp = textureView.getBitmap();
//        if (bmp == null) return;
//        Mat mat = new Mat();
//        Utils.bitmapToMat(bmp, mat);
//        Imgproc.cvtColor(mat, mat, Imgproc.COLOR_RGBA2GRAY);
//
//        Mat lap = new Mat();
//        Imgproc.Laplacian(mat, lap, CvType.CV_64F);
//        MatOfDouble mean = new MatOfDouble(), stddev = new MatOfDouble();
//        Core.meanStdDev(lap, mean, stddev);
//        double var = stddev.get(0, 0)[0];
//        lap.release(); mean.release(); stddev.release();
//
//        Core.meanStdDev(mat, mean, stddev);
//        double brightness = mean.get(0, 0)[0];
//        mean.release(); stddev.release();
//
//        double motionPercent;
//        if (previousGray != null) {
//            Mat diff = new Mat();
//            Core.absdiff(mat, previousGray, diff);
//            Imgproc.threshold(diff, diff, 15, 255, Imgproc.THRESH_BINARY);
//            motionPercent = Core.countNonZero(diff) * 100.0 / (diff.rows() * diff.cols());
//            diff.release();
//        } else {
//            motionPercent = 0;
//        }
//        if (previousGray != null) previousGray.release();
//        previousGray = mat.clone();
//        mat.release();
//
//        if (motionPercent > MOTION_THRESHOLD_PERCENT) {
//            recommendedExposureUs = MIN_EXP;
//        } else {
//            double scale = TARGET_LAPLACIAN_VAR / (var + 1e-6);
//            long ne = (long) (recommendedExposureUs * scale);
//            recommendedExposureUs = Math.min(MAX_EXP, Math.max(MIN_EXP, ne));
//            if (brightness < TARGET_BRIGHTNESS) {
//                recommendedIso = Math.min(MAX_ISO, recommendedIso * 2);
//            }
//        }
//
//        runOnUiThread(() -> {
//            motionParameterText.setText(String.format(Locale.getDefault(),
//                    "Motion:%.1f%%, BlurVar:%.1f, Bright:%.1f, ISO:%d",
//                    motionPercent, var, brightness, recommendedIso));
//            shutterSpeedText.setText(String.format(Locale.getDefault(),
//                    "Shutter: %d ms", recommendedExposureUs / 1000000));
//        });
//    }
//
//    private void captureImage() {
//        try {
//            CaptureRequest.Builder cap = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
//            cap.addTarget(captureReader.getSurface());
//            cap.set(CaptureRequest.CONTROL_MODE, CameraMetadata.CONTROL_MODE_OFF);
//            cap.set(CaptureRequest.CONTROL_AE_MODE, CameraMetadata.CONTROL_AE_MODE_OFF);
//            cap.set(CaptureRequest.SENSOR_EXPOSURE_TIME, recommendedExposureUs);
//            cap.set(CaptureRequest.SENSOR_SENSITIVITY, recommendedIso);
//            session.capture(cap.build(), null, null);
//
//            captureReader.setOnImageAvailableListener(reader -> {
//                Image img = reader.acquireNextImage();
//                ByteBuffer buffer = img.getPlanes()[0].getBuffer();
//                byte[] raw = new byte[buffer.remaining()];
//                buffer.get(raw);
//                saveImage(raw);
//                img.close();
//            }, null);
//        } catch (Exception e) {
//            Log.e("CamAct", "capture", e);
//        }
//    }
//
//    private void saveImage(byte[] data) {
//        try {
//            Bitmap bmp = BitmapFactory.decodeByteArray(data, 0, data.length);
//            ByteArrayOutputStream baos = new ByteArrayOutputStream();
//            bmp.compress(Bitmap.CompressFormat.JPEG, 95, baos);
//            byte[] finalBytes = baos.toByteArray();
//
//            String ts = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date());
//            ContentValues cv = new ContentValues();
//            cv.put(MediaStore.Images.Media.DISPLAY_NAME, "IMG_" + ts + ".jpg");
//            cv.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
//            cv.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/BlurControl");
//            Uri uri = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, cv);
//            try (FileOutputStream fos = (FileOutputStream) getContentResolver().openOutputStream(uri)) {
//                fos.write(finalBytes);
//            }
//        } catch (Exception e) {
//            Log.e("CamAct", "save", e);
//        }
//    }
//}
