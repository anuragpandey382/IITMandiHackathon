package com.example.veinscope;

import android.os.Bundle;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import com.bumptech.glide.Glide;
import android.widget.Button; // Add this line


public class ResponseActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_response);

        ImageView ivCaptured = findViewById(R.id.ivCaptured);
        ImageView ivResult = findViewById(R.id.ivResult);
        TextView tvDetails = findViewById(R.id.tvDetails);

        Button btnBack = findViewById(R.id.btnBack);
        btnBack.setOnClickListener(v -> {
            // Close this activity and return to MainActivity
            finish();
        });

        // Get image URLs from intent
//        String capturedUrl = getIntent().getStringExtra("CAPTURED_IMAGE_URL");
//        String resultUrl = getIntent().getStringExtra("RESULT_IMAGE_URL");
        String capturedUrl = getIntent().getStringExtra("CAPTURED_URL");
        String resultUrl   = getIntent().getStringExtra("RESULT_URL");


        // Load images using Glide
        Glide.with(this).load(capturedUrl).into(ivCaptured);
        Glide.with(this).load(resultUrl).into(ivResult);

        // Display additional details
        tvDetails.setText("Captured Image URL: " + capturedUrl + "\n\nResult Image URL: " + resultUrl);
    }

    // Add this method to handle the back button
    // Handle system back button
    @Override
    public void onBackPressed() {
        super.onBackPressed();  // Close this activity and return to MainActivity
    }
}