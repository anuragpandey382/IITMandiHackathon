import 'dart:convert';

import 'package:fakeit/config/secreats.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;

class FakeItHomePage extends StatefulWidget {
  const FakeItHomePage({super.key});

  @override
  _FakeItHomePageState createState() => _FakeItHomePageState();
}

class _FakeItHomePageState extends State<FakeItHomePage> {
  String? selectedFileName;
  bool _isLoading = false;
  String predict = "";

  _predictWav() async {
    _isLoading = true;
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('http://${Secreat.server}/cgi-bin/predict1.py'),
      );
      request.files.add(
        await http.MultipartFile.fromPath('audio_file', '$selectedFileName'),
      );

      http.StreamedResponse response = await request.send();

      if (response.statusCode == 200) {
        String res = await response.stream.bytesToString();
        print("Response: $res");
        predict = json.decode(res)["prediction"].toString();
      } else {
        print(response.reasonPhrase);
      }
    } catch (e) {
      _isLoading = false;
    }

    _isLoading = false;
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Container(
          margin: EdgeInsets.all(20),
          padding: EdgeInsets.all(30),
          decoration: BoxDecoration(
            color: Color(0xFF1E1E1E),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                "Fakeit",
                style: GoogleFonts.orbitron(
                  fontSize: 32,
                  color: Colors.cyanAccent,
                  fontWeight: FontWeight.bold,
                  shadows: [
                    Shadow(
                      color: Colors.cyanAccent.withOpacity(0.6),
                      blurRadius: 20,
                    ),
                  ],
                ),
              ),
              SizedBox(height: 8),
              Text(
                "AUDIO FAKE DETECTION",
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.2,
                ),
              ),
              SizedBox(height: 30),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  "Select audio file to analyze",
                  style: TextStyle(fontSize: 16),
                ),
              ),
              SizedBox(height: 10),
              Row(
                children: [
                  ElevatedButton(
                    onPressed: () async {
                      FilePickerResult? result = await FilePicker.platform
                          .pickFiles(type: FileType.audio);
                      print("Selected file: $result");
                      if (result != null) {
                        setState(() {
                          selectedFileName = result.files.single.path;
                        });
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.cyanAccent,
                      foregroundColor: Colors.black,
                      padding: EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 14,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: Text("Choose file"),
                  ),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      selectedFileName ?? "No file chosen",
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(color: Colors.white),
                    ),
                  ),
                ],
              ),
              SizedBox(height: 20),
              Divider(),
              ElevatedButton(
                onPressed:
                    selectedFileName == null
                        ? null
                        : _predictWav, // Disabled button
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.cyanAccent,
                  foregroundColor: Colors.black,
                  // backgroundColor: Colors.tealAccent.withOpacity(0.3),
                  padding: EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child:
                    _isLoading
                        ? CircularProgressIndicator()
                        : Text(
                          "Check if Audio is Fake",
                          style: TextStyle(color: Colors.black),
                        ),
              ),
              SizedBox(height: 20),
              Container(
                height: 50,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Color(0xFF2A2A2A),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: Text(predict, style: TextStyle(color: Colors.white)),
                ),
              ),
              SizedBox(height: 20),
              Text(
                "Supported audio types only.\nSelect a file, listen, then tap the button to check if the audio is fake or not.\n(This demo uses a simulated detection logic.)",
                style: TextStyle(fontSize: 12, color: Colors.white70),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
