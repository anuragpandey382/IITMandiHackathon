package com.example.hackethon;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.widget.Button;
import android.widget.ImageView;

import androidx.appcompat.app.AppCompatActivity;

public class MenuActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_menu);

        ImageView imgStartCamera = findViewById(R.id.imgStartCamera);
        ImageView imgSettings = findViewById(R.id.imgSettings);

        imgStartCamera.setOnClickListener(v -> {
            try {
                startActivity(new Intent(MenuActivity.this, CameraActivity.class));
            } catch (Exception e) {
                e.printStackTrace();
            }
        });

        imgSettings.setOnClickListener(v -> {
            try {
                startActivity(new Intent(MenuActivity.this, NormalCameraActivity.class));
            } catch (Exception e) {
                e.printStackTrace();
            }
        });

    }
}
