import 'package:fakeit/detect_on_file/fake_it.dart';
import 'package:fakeit/live_call_detection/live_call_detect.dart';
import 'package:flutter/material.dart';

void main() {
  runApp(MaterialApp(home: MyApp()));
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: Drawer(
        child: Column(
          children: [
            Image.asset("assets/logo.jpg"),
            Card(
              child: ListTile(
                title: Text("Live Call"),
                trailing: Icon(Icons.arrow_right),
                onTap:
                    () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (context) => LiveCallDetect()),
                    ),
              ),
            ),
          ],
        ),
      ),
      appBar: AppBar(title: Text("FackeIT- Fake Detector")),
      body: FakeItHomePage(),
    );
  }
}
