// // // // // // import 'dart:async';
// // // // // // import 'dart:io';
// // // // // // import 'dart:typed_data';
// // // // // // import 'package:flutter/material.dart';
// // // // // // import 'package:http/http.dart' as http;
// // // // // // import 'package:image_picker/image_picker.dart';
// // // // // // import 'package:video_player/video_player.dart';
// // // // // // import 'package:path_provider/path_provider.dart';
// // // // // //
// // // // // // const Color darkBackground = Color(0xFF181818);
// // // // // // const Color tealButtonAppbar = Color(0xFF6F9F9C);
// // // // // //
// // // // // // void main() => runApp(const PikachooApp());
// // // // // //
// // // // // //
// // // // // // class PikachooApp extends StatefulWidget {
// // // // // //   const PikachooApp({super.key});
// // // // // //   @override
// // // // // //   State<PikachooApp> createState() => _PikachooAppState();
// // // // // // }
// // // // // //
// // // // // // class _PikachooAppState extends State<PikachooApp> {
// // // // // //   ThemeMode _themeMode = ThemeMode.dark;
// // // // // //
// // // // // //   void _toggleTheme() {
// // // // // //     setState(() {
// // // // // //       _themeMode =
// // // // // //       _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
// // // // // //     });
// // // // // //   }
// // // // // //
// // // // // //   @override
// // // // // //   Widget build(BuildContext context) {
// // // // // //     return MaterialApp(
// // // // // //       debugShowCheckedModeBanner: false,
// // // // // //       themeMode: _themeMode,
// // // // // //       theme: ThemeData(
// // // // // //         brightness: Brightness.light,
// // // // // //         scaffoldBackgroundColor: Colors.white,
// // // // // //         primaryColor: tealButtonAppbar,
// // // // // //         appBarTheme: const AppBarTheme(
// // // // // //           backgroundColor: tealButtonAppbar,
// // // // // //           iconTheme: IconThemeData(color: Colors.white),
// // // // // //           titleTextStyle:
// // // // // //           TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20),
// // // // // //         ),
// // // // // //       ),
// // // // // //       darkTheme: ThemeData(
// // // // // //         brightness: Brightness.dark,
// // // // // //         scaffoldBackgroundColor: darkBackground,
// // // // // //         primaryColor: tealButtonAppbar,
// // // // // //         appBarTheme: const AppBarTheme(
// // // // // //           backgroundColor: tealButtonAppbar,
// // // // // //           iconTheme: IconThemeData(color: Colors.white),
// // // // // //           titleTextStyle:
// // // // // //           TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20),
// // // // // //         ),
// // // // // //       ),
// // // // // //       home: VideoUploader(onToggleTheme: _toggleTheme, themeMode: _themeMode),
// // // // // //     );
// // // // // //   }
// // // // // // }
// // // // // //
// // // // // // class VideoUploader extends StatefulWidget {
// // // // // //   final VoidCallback onToggleTheme;
// // // // // //   final ThemeMode themeMode;
// // // // // //
// // // // // //   const VideoUploader({super.key, required this.onToggleTheme, required this.themeMode});
// // // // // //
// // // // // //   @override
// // // // // //   State<VideoUploader> createState() => _VideoUploaderState();
// // // // // // }
// // // // // //
// // // // // // class _VideoUploaderState extends State<VideoUploader> {
// // // // // //   File? _pickedMedia;
// // // // // //   VideoPlayerController? _controller;
// // // // // //   final ImagePicker picker = ImagePicker();
// // // // // //   double _confidence = 50;
// // // // // //   double _threshold = 50;
// // // // // //
// // // // // //   Future<void> _pickFromGallery() async {
// // // // // //     final pickedFile = await picker.pickVideo(source: ImageSource.gallery);
// // // // // //     if (pickedFile != null) {
// // // // // //       await _handleMedia(File(pickedFile.path));
// // // // // //     }
// // // // // //   }
// // // // // //
// // // // // //   Future<void> _captureFromCamera() async {
// // // // // //     final XFile? capturedFile = await picker.pickVideo(source: ImageSource.camera);
// // // // // //     if (capturedFile != null) {
// // // // // //       await _handleMedia(File(capturedFile.path));
// // // // // //     }
// // // // // //   }
// // // // // //   Future<void> _handleMedia(File file) async {
// // // // // //     setState(() => _pickedMedia = file);
// // // // // //
// // // // // //     final request = http.MultipartRequest(
// // // // // //       'POST',
// // // // // //       Uri.parse('http://172.18.40.127:5000/detect'),
// // // // // //     );
// // // // // //
// // // // // //     // Add the video file
// // // // // //     request.files.add(await http.MultipartFile.fromPath('file', file.path));
// // // // // //
// // // // // //     // Convert percentage sliders to decimals and add to request
// // // // // //     request.fields['confidence_score'] = (_confidence / 100).toStringAsFixed(2);
// // // // // //     request.fields['threshold'] = (_threshold / 100).toStringAsFixed(2);
// // // // // //
// // // // // //     final response = await request.send();
// // // // // //
// // // // // //     if (response.statusCode == 200) {
// // // // // //       Uint8List bytes = await response.stream.toBytes();
// // // // // //       final tempDir = await getTemporaryDirectory();
// // // // // //       final processedFile = File('${tempDir.path}/output.mp4');
// // // // // //       await processedFile.writeAsBytes(bytes);
// // // // // //       setState(() => _pickedMedia = processedFile);
// // // // // //
// // // // // //       _controller?.dispose();
// // // // // //       _controller = VideoPlayerController.file(_pickedMedia!)
// // // // // //         ..initialize().then((_) => setState(() {}));
// // // // // //     } else {
// // // // // //       ScaffoldMessenger.of(context).showSnackBar(
// // // // // //         SnackBar(content: Text('Server Error: ${response.statusCode}')),
// // // // // //       );
// // // // // //     }
// // // // // //   }
// // // // // //
// // // // // //   void _showMediaOptions() {
// // // // // //     showDialog(
// // // // // //       context: context,
// // // // // //       builder: (context) => Dialog(
// // // // // //         shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
// // // // // //         child: Container(
// // // // // //           color: Colors.black,
// // // // // //           padding: const EdgeInsets.all(20),
// // // // // //           child: Column(
// // // // // //             mainAxisSize: MainAxisSize.min,
// // // // // //             children: [
// // // // // //               const Text(
// // // // // //                 'Select Media',
// // // // // //                 style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white),
// // // // // //               ),
// // // // // //               const SizedBox(height: 20),
// // // // // //               ElevatedButton.icon(
// // // // // //                 onPressed: () {
// // // // // //                   Navigator.pop(context);
// // // // // //                   _pickFromGallery();
// // // // // //                 },
// // // // // //                 icon: const Icon(Icons.photo),
// // // // // //                 label: const Text('Gallery'),
// // // // // //                 style: ElevatedButton.styleFrom(
// // // // // //                   backgroundColor: tealButtonAppbar,
// // // // // //                   foregroundColor: Colors.white,
// // // // // //                   minimumSize: const Size.fromHeight(45),
// // // // // //                   shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
// // // // // //                 ),
// // // // // //               ),
// // // // // //               const SizedBox(height: 10),
// // // // // //               ElevatedButton.icon(
// // // // // //                 onPressed: () {
// // // // // //                   Navigator.pop(context);
// // // // // //                   _captureFromCamera();
// // // // // //                 },
// // // // // //                 icon: const Icon(Icons.camera_alt),
// // // // // //                 label: const Text('Camera'),
// // // // // //                 style: ElevatedButton.styleFrom(
// // // // // //                   backgroundColor: tealButtonAppbar,
// // // // // //                   foregroundColor: Colors.white,
// // // // // //                   minimumSize: const Size.fromHeight(45),
// // // // // //                   shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
// // // // // //                 ),
// // // // // //               ),
// // // // // //             ],
// // // // // //           ),
// // // // // //         ),
// // // // // //       ),
// // // // // //     );
// // // // // //   }
// // // // // //   String _selectedOption = 'Object Detection';
// // // // // //
// // // // // //   Widget _buildOptionButton(String label) {
// // // // // //     final isSelected = label == _selectedOption;
// // // // // //
// // // // // //     return Padding(
// // // // // //       padding: const EdgeInsets.only(right: 8),
// // // // // //       child: OutlinedButton(
// // // // // //         onPressed: () {
// // // // // //           setState(() {
// // // // // //             _selectedOption = label;
// // // // // //           });
// // // // // //           ScaffoldMessenger.of(context).showSnackBar(
// // // // // //             SnackBar(content: Text('$label selected')),
// // // // // //           );
// // // // // //         },
// // // // // //         style: OutlinedButton.styleFrom(
// // // // // //           side: BorderSide(color: tealButtonAppbar),
// // // // // //           backgroundColor: isSelected ? tealButtonAppbar : Colors.transparent,
// // // // // //           foregroundColor: Colors.white,
// // // // // //           padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
// // // // // //           shape: RoundedRectangleBorder(
// // // // // //             borderRadius: BorderRadius.circular(6),
// // // // // //           ),
// // // // // //         ),
// // // // // //         child: Text(label),
// // // // // //       ),
// // // // // //     );
// // // // // //   }
// // // // // //
// // // // // //   bool _showControls = false;
// // // // // //   Timer? _hideTimer;
// // // // // //
// // // // // //
// // // // // //   Widget _mediaWidget() {
// // // // // //     if (_controller == null || !_controller!.value.isInitialized) {
// // // // // //       return const Padding(
// // // // // //         padding: EdgeInsets.symmetric(vertical: 20),
// // // // // //         child: Text(
// // // // // //           'Processed media will appear here.',
// // // // // //           style: TextStyle(color: Colors.white, fontSize: 16),
// // // // // //         ),
// // // // // //       );
// // // // // //     }
// // // // // //
// // // // // //     final videoSize = _controller!.value.size;
// // // // // //
// // // // // //     return GestureDetector(
// // // // // //         onTap: () {
// // // // // //           setState(() => _showControls = !_showControls);
// // // // // //           if (_showControls) {
// // // // // //             _startHideTimer();
// // // // // //           } else {
// // // // // //             _hideTimer?.cancel();
// // // // // //           }
// // // // // //         },
// // // // // //       child: Container(
// // // // // //         decoration: BoxDecoration(
// // // // // //           border: Border.all(color: Colors.white, width: 2),
// // // // // //           borderRadius: BorderRadius.circular(8),
// // // // // //         ),
// // // // // //         padding: const EdgeInsets.all(8),
// // // // // //         child: Stack(
// // // // // //           alignment: Alignment.center,
// // // // // //           children: [
// // // // // //             FittedBox(
// // // // // //               fit: BoxFit.contain,
// // // // // //               child: SizedBox(
// // // // // //                 width: videoSize.width,
// // // // // //                 height: videoSize.height,
// // // // // //                 child: VideoPlayer(_controller!),
// // // // // //               ),
// // // // // //             ),
// // // // // //             if (_showControls) ...[
// // // // // //               // Center Play/Pause Button
// // // // // //               IconButton(
// // // // // //                 iconSize: 64,
// // // // // //                 icon: Icon(
// // // // // //                   _controller!.value.isPlaying ? Icons.pause_circle : Icons.play_circle,
// // // // // //                   color: Colors.white,
// // // // // //                 ),
// // // // // //                 onPressed: () {
// // // // // //                   setState(() {
// // // // // //                     _controller!.value.isPlaying ? _controller!.pause() : _controller!.play();
// // // // // //                   });
// // // // // //                   _startHideTimer();
// // // // // //                 },
// // // // // //               ),
// // // // // //               // Bottom Row: Slider + Fullscreen Icon
// // // // // //               Positioned(
// // // // // //                 bottom: 0,
// // // // // //                 left: 0,
// // // // // //                 right: 0,
// // // // // //                 child: Row(
// // // // // //                   children: [
// // // // // //                     Expanded(
// // // // // //                       child: ValueListenableBuilder(
// // // // // //                         valueListenable: _controller!,
// // // // // //                         builder: (context, VideoPlayerValue value, child) {
// // // // // //                           final duration = value.duration.inMilliseconds;
// // // // // //                           final position = value.position.inMilliseconds;
// // // // // //
// // // // // //                           return Slider(
// // // // // //                             value: position.toDouble().clamp(0, duration.toDouble()),
// // // // // //                             min: 0,
// // // // // //                             max: duration.toDouble(),
// // // // // //                             activeColor: tealButtonAppbar,
// // // // // //                             inactiveColor: Colors.grey,
// // // // // //                             onChanged: (newValue) {
// // // // // //                               _controller!.seekTo(Duration(milliseconds: newValue.toInt()));
// // // // // //                               _startHideTimer();
// // // // // //                             },
// // // // // //                             onChangeStart: (_) => _hideTimer?.cancel(),
// // // // // //                             onChangeEnd: (_) => _startHideTimer(),
// // // // // //                           );
// // // // // //                         },
// // // // // //                       ),
// // // // // //                     ),
// // // // // //                     IconButton(
// // // // // //                       icon: const Icon(Icons.fullscreen, color: Colors.white),
// // // // // //                       onPressed: () {
// // // // // //                         Navigator.push(
// // // // // //                           context,
// // // // // //                           MaterialPageRoute(
// // // // // //                             builder: (_) => FullscreenVideoPage(controller: _controller!),
// // // // // //                           ),
// // // // // //                         );
// // // // // //                       },
// // // // // //                     ),
// // // // // //                   ],
// // // // // //                 ),
// // // // // //               ),
// // // // // //             ],
// // // // // //           ],
// // // // // //         ),
// // // // // //       ),
// // // // // //     );
// // // // // //   }
// // // // // //
// // // // // //
// // // // // //   void _startHideTimer() {
// // // // // //     _hideTimer?.cancel();
// // // // // //     _hideTimer = Timer(const Duration(seconds: 3), () {
// // // // // //       setState(() => _showControls = false);
// // // // // //     });
// // // // // //   }
// // // // // //
// // // // // //
// // // // // //
// // // // // //   Widget _buildBoundingBox(Size videoSize, List<Rect> detectedBoxes) {
// // // // // //     return Stack(
// // // // // //       children: detectedBoxes.map((rect) {
// // // // // //         final width = rect.width * videoSize.width;
// // // // // //         final height = rect.height * videoSize.height;
// // // // // //         final left = rect.left * videoSize.width;
// // // // // //         final top = rect.top * videoSize.height;
// // // // // //         return Positioned(
// // // // // //           left: left,
// // // // // //           top: top,
// // // // // //           child: Container(
// // // // // //             width: width,
// // // // // //             height: height,
// // // // // //             decoration: BoxDecoration(
// // // // // //               border: Border.all(color: Colors.green, width: 2),
// // // // // //             ),
// // // // // //           ),
// // // // // //         );
// // // // // //       }).toList(),
// // // // // //     );
// // // // // //   }
// // // // // //
// // // // // //   @override
// // // // // //   void dispose() {
// // // // // //     _controller?.dispose();
// // // // // //     _hideTimer?.cancel();
// // // // // //     super.dispose();
// // // // // //   }
// // // // // //
// // // // // //   @override
// // // // // //   Widget build(BuildContext context) {
// // // // // //     bool isDark = widget.themeMode == ThemeMode.dark;
// // // // // //
// // // // // //     return Scaffold(
// // // // // //       appBar: AppBar(
// // // // // //         title: const Text('Pikachoo'),
// // // // // //         actions: [
// // // // // //           IconButton(
// // // // // //             icon: Icon(
// // // // // //               isDark ? Icons.wb_sunny : Icons.nightlight_round,
// // // // // //               color: Colors.white,
// // // // // //             ),
// // // // // //             onPressed: widget.onToggleTheme,
// // // // // //             tooltip: isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode',
// // // // // //           ),
// // // // // //         ],
// // // // // //       ),
// // // // // //       body: SingleChildScrollView(
// // // // // //         child: Column(
// // // // // //           children: [
// // // // // //             const SizedBox(height: 16),
// // // // // //             Center(child: _mediaWidget()),
// // // // // //             const SizedBox(height: 10),
// // // // // //             if (_controller != null && _controller!.value.isInitialized)
// // // // // //             const SizedBox(height: 20),
// // // // // //             SingleChildScrollView(
// // // // // //               scrollDirection: Axis.horizontal,
// // // // // //               padding: const EdgeInsets.symmetric(horizontal: 8),
// // // // // //               child: Row(
// // // // // //                 children: [
// // // // // //                   _buildOptionButton('Object Detection'),
// // // // // //                   _buildOptionButton('Object Tracking'),
// // // // // //                   _buildOptionButton('Stampede Detection'),
// // // // // //                   _buildOptionButton('More1'),
// // // // // //                   _buildOptionButton('More2'),
// // // // // //                 ],
// // // // // //               ),
// // // // // //             ),
// // // // // //             const SizedBox(height: 20),
// // // // // //             Slider(
// // // // // //               value: _confidence,
// // // // // //               min: 0,
// // // // // //               max: 100,
// // // // // //               divisions: 100,
// // // // // //               activeColor: tealButtonAppbar,
// // // // // //               label: '${_confidence.toStringAsFixed(0)}%',
// // // // // //               onChanged: (value) {
// // // // // //                 setState(() {
// // // // // //                   _confidence = value;
// // // // // //                 });
// // // // // //               },
// // // // // //             ),
// // // // // //             Text(
// // // // // //               'Confidence: ${_confidence.toStringAsFixed(0)}%',
// // // // // //               style: const TextStyle(color: Colors.white),
// // // // // //             ),
// // // // // //             const SizedBox(height: 20),
// // // // // //             Slider(
// // // // // //               value: _threshold,
// // // // // //               min: 0,
// // // // // //               max: 100,
// // // // // //               divisions: 100,
// // // // // //               activeColor: tealButtonAppbar,
// // // // // //               label: '${_threshold.toStringAsFixed(0)}%',
// // // // // //               onChanged: (value) {
// // // // // //                 setState(() {
// // // // // //                   _threshold = value;
// // // // // //                 });
// // // // // //               },
// // // // // //             ),
// // // // // //             Text(
// // // // // //               'Threshold: ${_threshold.toStringAsFixed(0)}%',
// // // // // //               style: const TextStyle(color: Colors.white),
// // // // // //             ),
// // // // // //             const SizedBox(height: 30),
// // // // // //           ],
// // // // // //         ),
// // // // // //       ),
// // // // // //       bottomNavigationBar: Padding(
// // // // // //         padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
// // // // // //         child: ElevatedButton.icon(
// // // // // //           onPressed: _showMediaOptions,
// // // // // //           icon: const Icon(Icons.upload_file),
// // // // // //           label: const Text('Upload'),
// // // // // //           style: ElevatedButton.styleFrom(
// // // // // //             minimumSize: const Size.fromHeight(50),
// // // // // //             backgroundColor: tealButtonAppbar,
// // // // // //             foregroundColor: Colors.white,
// // // // // //             shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
// // // // // //           ),
// // // // // //         ),
// // // // // //       ),
// // // // // //     );
// // // // // //   }
// // // // // // }
// // // // // //
// // // // // //
// // // // // // class FullscreenVideoPage extends StatefulWidget {
// // // // // //   final VideoPlayerController controller;
// // // // // //
// // // // // //   const FullscreenVideoPage({super.key, required this.controller});
// // // // // //
// // // // // //   @override
// // // // // //   State<FullscreenVideoPage> createState() => _FullscreenVideoPageState();
// // // // // // }
// // // // // //
// // // // // // class _FullscreenVideoPageState extends State<FullscreenVideoPage> {
// // // // // //   bool _showControls = true;
// // // // // //   Timer? _hideTimer;
// // // // // //
// // // // // //   @override
// // // // // //   void initState() {
// // // // // //     super.initState();
// // // // // //     _startHideTimer();
// // // // // //   }
// // // // // //
// // // // // //   void _startHideTimer() {
// // // // // //     _hideTimer?.cancel();
// // // // // //     _hideTimer = Timer(const Duration(seconds: 3), () {
// // // // // //       setState(() => _showControls = false);
// // // // // //     });
// // // // // //   }
// // // // // //
// // // // // //   @override
// // // // // //   void dispose() {
// // // // // //     _hideTimer?.cancel();
// // // // // //     super.dispose();
// // // // // //   }
// // // // // //
// // // // // //   @override
// // // // // //   Widget build(BuildContext context) {
// // // // // //     final controller = widget.controller;
// // // // // //
// // // // // //     return Scaffold(
// // // // // //       backgroundColor: Colors.black,
// // // // // //       body: GestureDetector(
// // // // // //         onTap: () {
// // // // // //           setState(() => _showControls = !_showControls);
// // // // // //           if (_showControls) {
// // // // // //             _startHideTimer();
// // // // // //           } else {
// // // // // //             _hideTimer?.cancel();
// // // // // //           }
// // // // // //         },
// // // // // //         child: Stack(
// // // // // //           alignment: Alignment.center,
// // // // // //           children: [
// // // // // //             Center(
// // // // // //               child: AspectRatio(
// // // // // //                 aspectRatio: controller.value.aspectRatio,
// // // // // //                 child: VideoPlayer(controller),
// // // // // //               ),
// // // // // //             ),
// // // // // //             if (_showControls) ...[
// // // // // //               // Play/Pause in center
// // // // // //               IconButton(
// // // // // //                 iconSize: 64,
// // // // // //                 icon: Icon(
// // // // // //                   controller.value.isPlaying ? Icons.pause_circle : Icons.play_circle,
// // // // // //                   color: Colors.white,
// // // // // //                 ),
// // // // // //                 onPressed: () {
// // // // // //                   setState(() {
// // // // // //                     controller.value.isPlaying ? controller.pause() : controller.play();
// // // // // //                   });
// // // // // //                   _startHideTimer();
// // // // // //                 },
// // // // // //               ),
// // // // // //               // Slider and Close Button at bottom
// // // // // //               Positioned(
// // // // // //                 bottom: 0,
// // // // // //                 left: 0,
// // // // // //                 right: 0,
// // // // // //                 child: Row(
// // // // // //                   children: [
// // // // // //                     Expanded(
// // // // // //                       child: ValueListenableBuilder(
// // // // // //                         valueListenable: controller,
// // // // // //                         builder: (context, VideoPlayerValue value, child) {
// // // // // //                           final duration = value.duration.inMilliseconds;
// // // // // //                           final position = value.position.inMilliseconds;
// // // // // //
// // // // // //                           return Slider(
// // // // // //                             value: position.toDouble().clamp(0, duration.toDouble()),
// // // // // //                             min: 0,
// // // // // //                             max: duration.toDouble(),
// // // // // //                             activeColor: Colors.teal,
// // // // // //                             inactiveColor: Colors.grey,
// // // // // //                             onChanged: (newValue) {
// // // // // //                               controller.seekTo(Duration(milliseconds: newValue.toInt()));
// // // // // //                               _startHideTimer();
// // // // // //                             },
// // // // // //                             onChangeStart: (_) => _hideTimer?.cancel(),
// // // // // //                             onChangeEnd: (_) => _startHideTimer(),
// // // // // //                           );
// // // // // //                         },
// // // // // //                       ),
// // // // // //                     ),
// // // // // //                     IconButton(
// // // // // //                       icon: const Icon(Icons.close_fullscreen, color: Colors.white),
// // // // // //                       onPressed: () => Navigator.pop(context),
// // // // // //                     ),
// // // // // //                   ],
// // // // // //                 ),
// // // // // //               ),
// // // // // //             ],
// // // // // //           ],
// // // // // //         ),
// // // // // //       ),
// // // // // //     );
// // // // // //   }
// // // // // // }
// // // // //
// // // // //
// // // // // // Your imports remain unchanged
// // // // // import 'dart:async';
// // // // // import 'dart:io';
// // // // // import 'dart:typed_data';
// // // // // import 'package:flutter/material.dart';
// // // // // import 'package:http/http.dart' as http;
// // // // // import 'package:image_picker/image_picker.dart';
// // // // // import 'package:video_player/video_player.dart';
// // // // // import 'package:path_provider/path_provider.dart';
// // // // //
// // // // // const Color darkBackground = Color(0xFF181818);
// // // // // const Color tealButtonAppbar = Color(0xFF6F9F9C);
// // // // //
// // // // // void main() => runApp(const PikachooApp());
// // // // //
// // // // // class PikachooApp extends StatefulWidget {
// // // // //   const PikachooApp({super.key});
// // // // //   @override
// // // // //   State<PikachooApp> createState() => _PikachooAppState();
// // // // // }
// // // // //
// // // // // class _PikachooAppState extends State<PikachooApp> {
// // // // //   ThemeMode _themeMode = ThemeMode.dark;
// // // // //
// // // // //   void _toggleTheme() {
// // // // //     setState(() {
// // // // //       _themeMode =
// // // // //       _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
// // // // //     });
// // // // //   }
// // // // //
// // // // //   @override
// // // // //   Widget build(BuildContext context) {
// // // // //     return MaterialApp(
// // // // //       debugShowCheckedModeBanner: false,
// // // // //       themeMode: _themeMode,
// // // // //       theme: ThemeData(
// // // // //         brightness: Brightness.light,
// // // // //         scaffoldBackgroundColor: Colors.white,
// // // // //         primaryColor: tealButtonAppbar,
// // // // //         appBarTheme: const AppBarTheme(
// // // // //           backgroundColor: tealButtonAppbar,
// // // // //           iconTheme: IconThemeData(color: Colors.white),
// // // // //           titleTextStyle: TextStyle(
// // // // //               color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20),
// // // // //         ),
// // // // //       ),
// // // // //       darkTheme: ThemeData(
// // // // //         brightness: Brightness.dark,
// // // // //         scaffoldBackgroundColor: darkBackground,
// // // // //         primaryColor: tealButtonAppbar,
// // // // //         appBarTheme: const AppBarTheme(
// // // // //           backgroundColor: tealButtonAppbar,
// // // // //           iconTheme: IconThemeData(color: Colors.white),
// // // // //           titleTextStyle: TextStyle(
// // // // //               color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20),
// // // // //         ),
// // // // //       ),
// // // // //       home: VideoUploader(onToggleTheme: _toggleTheme, themeMode: _themeMode),
// // // // //     );
// // // // //   }
// // // // // }
// // // // //
// // // // // class VideoUploader extends StatefulWidget {
// // // // //   final VoidCallback onToggleTheme;
// // // // //   final ThemeMode themeMode;
// // // // //
// // // // //   const VideoUploader(
// // // // //       {super.key, required this.onToggleTheme, required this.themeMode});
// // // // //
// // // // //   @override
// // // // //   State<VideoUploader> createState() => _VideoUploaderState();
// // // // // }
// // // // //
// // // // // class _VideoUploaderState extends State<VideoUploader> {
// // // // //   File? _pickedMedia;
// // // // //   VideoPlayerController? _controller;
// // // // //   final ImagePicker picker = ImagePicker();
// // // // //   double _confidence = 50;
// // // // //   double _threshold = 50;
// // // // //   bool _loading = false;
// // // // //
// // // // //   Future<void> _pickFromGallery() async {
// // // // //     final pickedFile = await picker.pickVideo(source: ImageSource.gallery);
// // // // //     if (pickedFile != null) {
// // // // //       await _handleMedia(File(pickedFile.path));
// // // // //     }
// // // // //   }
// // // // //
// // // // //   Future<void> _captureFromCamera() async {
// // // // //     final XFile? capturedFile =
// // // // //     await picker.pickVideo(source: ImageSource.camera);
// // // // //     if (capturedFile != null) {
// // // // //       await _handleMedia(File(capturedFile.path));
// // // // //     }
// // // // //   }
// // // // //
// // // // //   Future<void> _handleMedia(File file) async {
// // // // //     setState(() {
// // // // //       _pickedMedia = file;
// // // // //       _loading = true;
// // // // //     });
// // // // //
// // // // //     final request = http.MultipartRequest(
// // // // //       'POST',
// // // // //       Uri.parse('http://172.18.40.127:5000/detect'),
// // // // //     );
// // // // //
// // // // //     request.files.add(await http.MultipartFile.fromPath('file', file.path));
// // // // //     request.fields['confidence_score'] =
// // // // //         (_confidence / 100).toStringAsFixed(2);
// // // // //     request.fields['threshold'] = (_threshold / 100).toStringAsFixed(2);
// // // // //
// // // // //     try {
// // // // //       final response = await request.send();
// // // // //       if (response.statusCode == 200) {
// // // // //         Uint8List bytes = await response.stream.toBytes();
// // // // //         final tempDir = await getTemporaryDirectory();
// // // // //         final processedFile = File('${tempDir.path}/output.mp4');
// // // // //         await processedFile.writeAsBytes(bytes);
// // // // //         _controller?.dispose();
// // // // //         _controller = VideoPlayerController.file(processedFile)
// // // // //           ..initialize().then((_) {
// // // // //             setState(() {
// // // // //               _pickedMedia = processedFile;
// // // // //               _loading = false;
// // // // //             });
// // // // //           });
// // // // //       } else {
// // // // //         setState(() => _loading = false);
// // // // //         ScaffoldMessenger.of(context).showSnackBar(
// // // // //           SnackBar(content: Text('Server Error: ${response.statusCode}')),
// // // // //         );
// // // // //       }
// // // // //     } catch (e) {
// // // // //       setState(() => _loading = false);
// // // // //       ScaffoldMessenger.of(context).showSnackBar(
// // // // //         SnackBar(content: Text('Upload failed: $e')),
// // // // //       );
// // // // //     }
// // // // //   }
// // // // //
// // // // //   void _showMediaOptions() {
// // // // //     showDialog(
// // // // //       context: context,
// // // // //       builder: (context) => Dialog(
// // // // //         shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
// // // // //         child: Container(
// // // // //           color: Colors.black,
// // // // //           padding: const EdgeInsets.all(20),
// // // // //           child: Column(
// // // // //             mainAxisSize: MainAxisSize.min,
// // // // //             children: [
// // // // //               const Text(
// // // // //                 'Select Media',
// // // // //                 style: TextStyle(
// // // // //                     fontWeight: FontWeight.bold,
// // // // //                     fontSize: 18,
// // // // //                     color: Colors.white),
// // // // //               ),
// // // // //               const SizedBox(height: 20),
// // // // //               ElevatedButton.icon(
// // // // //                 onPressed: () {
// // // // //                   Navigator.pop(context);
// // // // //                   _pickFromGallery();
// // // // //                 },
// // // // //                 icon: const Icon(Icons.photo),
// // // // //                 label: const Text('Gallery'),
// // // // //                 style: ElevatedButton.styleFrom(
// // // // //                   backgroundColor: tealButtonAppbar,
// // // // //                   foregroundColor: Colors.white,
// // // // //                   minimumSize: const Size.fromHeight(45),
// // // // //                   shape: RoundedRectangleBorder(
// // // // //                       borderRadius: BorderRadius.circular(4)),
// // // // //                 ),
// // // // //               ),
// // // // //               const SizedBox(height: 10),
// // // // //               ElevatedButton.icon(
// // // // //                 onPressed: () {
// // // // //                   Navigator.pop(context);
// // // // //                   _captureFromCamera();
// // // // //                 },
// // // // //                 icon: const Icon(Icons.camera_alt),
// // // // //                 label: const Text('Camera'),
// // // // //                 style: ElevatedButton.styleFrom(
// // // // //                   backgroundColor: tealButtonAppbar,
// // // // //                   foregroundColor: Colors.white,
// // // // //                   minimumSize: const Size.fromHeight(45),
// // // // //                   shape: RoundedRectangleBorder(
// // // // //                       borderRadius: BorderRadius.circular(4)),
// // // // //                 ),
// // // // //               ),
// // // // //             ],
// // // // //           ),
// // // // //         ),
// // // // //       ),
// // // // //     );
// // // // //   }
// // // // //
// // // // //   String _selectedOption = 'Object Detection';
// // // // //   bool _showControls = false;
// // // // //   Timer? _hideTimer;
// // // // //
// // // // //   Widget _mediaWidget() {
// // // // //     if (_controller == null || !_controller!.value.isInitialized) {
// // // // //       return const Padding(
// // // // //         padding: EdgeInsets.symmetric(vertical: 20),
// // // // //         child: Text(
// // // // //           'Processed media will appear here.',
// // // // //           style: TextStyle(color: Colors.white, fontSize: 16),
// // // // //         ),
// // // // //       );
// // // // //     }
// // // // //
// // // // //     final videoSize = _controller!.value.size;
// // // // //
// // // // //     return GestureDetector(
// // // // //       onTap: () {
// // // // //         setState(() => _showControls = !_showControls);
// // // // //         if (_showControls) {
// // // // //           _startHideTimer();
// // // // //         } else {
// // // // //           _hideTimer?.cancel();
// // // // //         }
// // // // //       },
// // // // //       child: Container(
// // // // //         decoration: BoxDecoration(
// // // // //           border: Border.all(color: Colors.white, width: 2),
// // // // //           borderRadius: BorderRadius.circular(8),
// // // // //         ),
// // // // //         padding: const EdgeInsets.all(8),
// // // // //         child: Stack(
// // // // //           alignment: Alignment.center,
// // // // //           children: [
// // // // //             FittedBox(
// // // // //               fit: BoxFit.contain,
// // // // //               child: SizedBox(
// // // // //                 width: videoSize.width,
// // // // //                 height: videoSize.height,
// // // // //                 child: VideoPlayer(_controller!),
// // // // //               ),
// // // // //             ),
// // // // //             if (_showControls) ...[
// // // // //               IconButton(
// // // // //                 iconSize: 64,
// // // // //                 icon: Icon(
// // // // //                   _controller!.value.isPlaying
// // // // //                       ? Icons.pause_circle
// // // // //                       : Icons.play_circle,
// // // // //                   color: Colors.white,
// // // // //                 ),
// // // // //                 onPressed: () {
// // // // //                   setState(() {
// // // // //                     _controller!.value.isPlaying
// // // // //                         ? _controller!.pause()
// // // // //                         : _controller!.play();
// // // // //                   });
// // // // //                   _startHideTimer();
// // // // //                 },
// // // // //               ),
// // // // //               Positioned(
// // // // //                 bottom: 0,
// // // // //                 left: 0,
// // // // //                 right: 0,
// // // // //                 child: Row(
// // // // //                   children: [
// // // // //                     Expanded(
// // // // //                       child: ValueListenableBuilder(
// // // // //                         valueListenable: _controller!,
// // // // //                         builder:
// // // // //                             (context, VideoPlayerValue value, child) {
// // // // //                           final duration =
// // // // //                               value.duration.inMilliseconds;
// // // // //                           final position =
// // // // //                               value.position.inMilliseconds;
// // // // //
// // // // //                           return Slider(
// // // // //                             value: position
// // // // //                                 .toDouble()
// // // // //                                 .clamp(0, duration.toDouble()),
// // // // //                             min: 0,
// // // // //                             max: duration.toDouble(),
// // // // //                             activeColor: tealButtonAppbar,
// // // // //                             inactiveColor: Colors.grey,
// // // // //                             onChanged: (newValue) {
// // // // //                               _controller!.seekTo(Duration(
// // // // //                                   milliseconds: newValue.toInt()));
// // // // //                               _startHideTimer();
// // // // //                             },
// // // // //                             onChangeStart: (_) =>
// // // // //                                 _hideTimer?.cancel(),
// // // // //                             onChangeEnd: (_) => _startHideTimer(),
// // // // //                           );
// // // // //                         },
// // // // //                       ),
// // // // //                     ),
// // // // //                     IconButton(
// // // // //                       icon: const Icon(Icons.fullscreen,
// // // // //                           color: Colors.white),
// // // // //                       onPressed: () {
// // // // //                         Navigator.push(
// // // // //                           context,
// // // // //                           MaterialPageRoute(
// // // // //                             builder: (_) => FullscreenVideoPage(
// // // // //                                 controller: _controller!),
// // // // //                           ),
// // // // //                         );
// // // // //                       },
// // // // //                     ),
// // // // //                   ],
// // // // //                 ),
// // // // //               ),
// // // // //             ],
// // // // //           ],
// // // // //         ),
// // // // //       ),
// // // // //     );
// // // // //   }
// // // // //
// // // // //   void _startHideTimer() {
// // // // //     _hideTimer?.cancel();
// // // // //     _hideTimer = Timer(const Duration(seconds: 3), () {
// // // // //       setState(() => _showControls = false);
// // // // //     });
// // // // //   }
// // // // //
// // // // //   @override
// // // // //   void dispose() {
// // // // //     _controller?.dispose();
// // // // //     _hideTimer?.cancel();
// // // // //     super.dispose();
// // // // //   }
// // // // //
// // // // //   @override
// // // // //   Widget build(BuildContext context) {
// // // // //     bool isDark = widget.themeMode == ThemeMode.dark;
// // // // //
// // // // //     return Scaffold(
// // // // //       appBar: AppBar(
// // // // //         title: const Text('Pikachoo'),
// // // // //         actions: [
// // // // //           IconButton(
// // // // //             icon: Icon(
// // // // //               isDark ? Icons.wb_sunny : Icons.nightlight_round,
// // // // //               color: Colors.white,
// // // // //             ),
// // // // //             onPressed: widget.onToggleTheme,
// // // // //             tooltip:
// // // // //             isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode',
// // // // //           ),
// // // // //         ],
// // // // //       ),
// // // // //       body: Stack(
// // // // //         children: [
// // // // //           SingleChildScrollView(
// // // // //             child: Column(
// // // // //               children: [
// // // // //                 const SizedBox(height: 16),
// // // // //                 Center(child: _mediaWidget()),
// // // // //                 const SizedBox(height: 10),
// // // // //                 SingleChildScrollView(
// // // // //                   scrollDirection: Axis.horizontal,
// // // // //                   padding: const EdgeInsets.symmetric(horizontal: 8),
// // // // //                   child: Row(
// // // // //                     children: [
// // // // //                       _buildOptionButton('Object Detection'),
// // // // //                       _buildOptionButton('Object Tracking'),
// // // // //                       _buildOptionButton('Stampede Detection'),
// // // // //                       _buildOptionButton('More1'),
// // // // //                       _buildOptionButton('More2'),
// // // // //                     ],
// // // // //                   ),
// // // // //                 ),
// // // // //                 const SizedBox(height: 20),
// // // // //                 Slider(
// // // // //                   value: _confidence,
// // // // //                   min: 0,
// // // // //                   max: 100,
// // // // //                   divisions: 100,
// // // // //                   activeColor: tealButtonAppbar,
// // // // //                   label: '${_confidence.toStringAsFixed(0)}%',
// // // // //                   onChanged: (value) {
// // // // //                     setState(() {
// // // // //                       _confidence = value;
// // // // //                     });
// // // // //                   },
// // // // //                 ),
// // // // //                 Text('Confidence: ${_confidence.toStringAsFixed(0)}%',
// // // // //                     style: const TextStyle(color: Colors.white)),
// // // // //                 const SizedBox(height: 20),
// // // // //                 Slider(
// // // // //                   value: _threshold,
// // // // //                   min: 0,
// // // // //                   max: 100,
// // // // //                   divisions: 100,
// // // // //                   activeColor: tealButtonAppbar,
// // // // //                   label: '${_threshold.toStringAsFixed(0)}%',
// // // // //                   onChanged: (value) {
// // // // //                     setState(() {
// // // // //                       _threshold = value;
// // // // //                     });
// // // // //                   },
// // // // //                 ),
// // // // //                 Text('Threshold: ${_threshold.toStringAsFixed(0)}%',
// // // // //                     style: const TextStyle(color: Colors.white)),
// // // // //                 const SizedBox(height: 30),
// // // // //               ],
// // // // //             ),
// // // // //           ),
// // // // //           if (_loading)
// // // // //             Container(
// // // // //               color: Colors.black.withOpacity(0.7),
// // // // //               child: const Center(
// // // // //                 child: CircularProgressIndicator(
// // // // //                   color: Colors.white,
// // // // //                   strokeWidth: 4,
// // // // //                 ),
// // // // //               ),
// // // // //             ),
// // // // //         ],
// // // // //       ),
// // // // //       bottomNavigationBar: Padding(
// // // // //         padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
// // // // //         child: ElevatedButton.icon(
// // // // //           onPressed: _showMediaOptions,
// // // // //           icon: const Icon(Icons.upload_file),
// // // // //           label: const Text('Upload'),
// // // // //           style: ElevatedButton.styleFrom(
// // // // //             minimumSize: const Size.fromHeight(50),
// // // // //             backgroundColor: tealButtonAppbar,
// // // // //             foregroundColor: Colors.white,
// // // // //             shape: RoundedRectangleBorder(
// // // // //                 borderRadius: BorderRadius.circular(4)),
// // // // //           ),
// // // // //         ),
// // // // //       ),
// // // // //     );
// // // // //   }
// // // // //
// // // // //   Widget _buildOptionButton(String label) {
// // // // //     final isSelected = label == _selectedOption;
// // // // //     return Padding(
// // // // //       padding: const EdgeInsets.only(right: 8),
// // // // //       child: OutlinedButton(
// // // // //         onPressed: () {
// // // // //           setState(() => _selectedOption = label);
// // // // //           ScaffoldMessenger.of(context).showSnackBar(
// // // // //             SnackBar(content: Text('$label selected')),
// // // // //           );
// // // // //         },
// // // // //         style: OutlinedButton.styleFrom(
// // // // //           side: BorderSide(color: tealButtonAppbar),
// // // // //           backgroundColor: isSelected ? tealButtonAppbar : Colors.transparent,
// // // // //           foregroundColor: Colors.white,
// // // // //           padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
// // // // //           shape: RoundedRectangleBorder(
// // // // //             borderRadius: BorderRadius.circular(6),
// // // // //           ),
// // // // //         ),
// // // // //         child: Text(label),
// // // // //       ),
// // // // //     );
// // // // //   }
// // // // // }
// // // // //
// // // // // class FullscreenVideoPage extends StatefulWidget {
// // // // //   final VideoPlayerController controller;
// // // // //   const FullscreenVideoPage({super.key, required this.controller});
// // // // //   @override
// // // // //   State<FullscreenVideoPage> createState() => _FullscreenVideoPageState();
// // // // // }
// // // // //
// // // // // class _FullscreenVideoPageState extends State<FullscreenVideoPage> {
// // // // //   bool _showControls = true;
// // // // //   Timer? _hideTimer;
// // // // //
// // // // //   @override
// // // // //   void initState() {
// // // // //     super.initState();
// // // // //     _startHideTimer();
// // // // //   }
// // // // //
// // // // //   void _startHideTimer() {
// // // // //     _hideTimer?.cancel();
// // // // //     _hideTimer = Timer(const Duration(seconds: 3), () {
// // // // //       setState(() => _showControls = false);
// // // // //     });
// // // // //   }
// // // // //
// // // // //   @override
// // // // //   void dispose() {
// // // // //     _hideTimer?.cancel();
// // // // //     super.dispose();
// // // // //   }
// // // // //
// // // // //   @override
// // // // //   Widget build(BuildContext context) {
// // // // //     final controller = widget.controller;
// // // // //     return Scaffold(
// // // // //       backgroundColor: Colors.black,
// // // // //       body: GestureDetector(
// // // // //         onTap: () {
// // // // //           setState(() => _showControls = !_showControls);
// // // // //           if (_showControls) {
// // // // //             _startHideTimer();
// // // // //           } else {
// // // // //             _hideTimer?.cancel();
// // // // //           }
// // // // //         },
// // // // //         child: Stack(
// // // // //           alignment: Alignment.center,
// // // // //           children: [
// // // // //             Center(
// // // // //               child: AspectRatio(
// // // // //                 aspectRatio: controller.value.aspectRatio,
// // // // //                 child: VideoPlayer(controller),
// // // // //               ),
// // // // //             ),
// // // // //             if (_showControls) ...[
// // // // //               IconButton(
// // // // //                 iconSize: 64,
// // // // //                 icon: Icon(
// // // // //                   controller.value.isPlaying
// // // // //                       ? Icons.pause_circle
// // // // //                       : Icons.play_circle,
// // // // //                   color: Colors.white,
// // // // //                 ),
// // // // //                 onPressed: () {
// // // // //                   setState(() {
// // // // //                     controller.value.isPlaying
// // // // //                         ? controller.pause()
// // // // //                         : controller.play();
// // // // //                   });
// // // // //                   _startHideTimer();
// // // // //                 },
// // // // //               ),
// // // // //               Positioned(
// // // // //                 bottom: 0,
// // // // //                 left: 0,
// // // // //                 right: 0,
// // // // //                 child: Row(
// // // // //                   children: [
// // // // //                     Expanded(
// // // // //                       child: ValueListenableBuilder(
// // // // //                         valueListenable: controller,
// // // // //                         builder:
// // // // //                             (context, VideoPlayerValue value, child) {
// // // // //                           final duration =
// // // // //                               value.duration.inMilliseconds;
// // // // //                           final position =
// // // // //                               value.position.inMilliseconds;
// // // // //                           return Slider(
// // // // //                             value: position
// // // // //                                 .toDouble()
// // // // //                                 .clamp(0, duration.toDouble()),
// // // // //                             min: 0,
// // // // //                             max: duration.toDouble(),
// // // // //                             activeColor: Colors.teal,
// // // // //                             inactiveColor: Colors.grey,
// // // // //                             onChanged: (newValue) {
// // // // //                               controller.seekTo(Duration(
// // // // //                                   milliseconds: newValue.toInt()));
// // // // //                               _startHideTimer();
// // // // //                             },
// // // // //                             onChangeStart: (_) =>
// // // // //                                 _hideTimer?.cancel(),
// // // // //                             onChangeEnd: (_) => _startHideTimer(),
// // // // //                           );
// // // // //                         },
// // // // //                       ),
// // // // //                     ),
// // // // //                     IconButton(
// // // // //                       icon: const Icon(Icons.close_fullscreen,
// // // // //                           color: Colors.white),
// // // // //                       onPressed: () => Navigator.pop(context),
// // // // //                     ),
// // // // //                   ],
// // // // //                 ),
// // // // //               ),
// // // // //             ],
// // // // //           ],
// // // // //         ),
// // // // //       ),
// // // // //     );
// // // // //   }
// // // // // }
// // // //
// // // //
// import 'dart:async';
// import 'dart:developer' as developer;
// import 'dart:io';
// import 'dart:typed_data';
// import 'package:flutter/material.dart';
// import 'package:http/http.dart' as http;
// import 'package:image_picker/image_picker.dart';
// import 'package:video_player/video_player.dart';
// import 'package:path_provider/path_provider.dart';
//
// const Color darkBackground = Color(0xFF181818);
// const Color tealButtonAppbar = Color(0xFF6F9F9C);
//
// void main() => runApp(const PikachooApp());
//
// class PikachooApp extends StatefulWidget {
//   const PikachooApp({super.key});
//   @override
//   State<PikachooApp> createState() => _PikachooAppState();
// }
//
// class _PikachooAppState extends State<PikachooApp> {
//   ThemeMode _themeMode = ThemeMode.dark;
//
//   void _toggleTheme() {
//     setState(() {
//       _themeMode =
//       _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
//     });
//   }
//
//   @override
//   Widget build(BuildContext context) {
//     return MaterialApp(
//       debugShowCheckedModeBanner: false,
//       themeMode: _themeMode,
//       theme: ThemeData(
//         brightness: Brightness.light,
//         scaffoldBackgroundColor: Colors.white,
//         primaryColor: tealButtonAppbar,
//         appBarTheme: const AppBarTheme(
//           backgroundColor: tealButtonAppbar,
//           iconTheme: IconThemeData(color: Colors.white),
//           titleTextStyle: TextStyle(
//               color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20),
//         ),
//       ),
//       darkTheme: ThemeData(
//         brightness: Brightness.dark,
//         scaffoldBackgroundColor: darkBackground,
//         primaryColor: tealButtonAppbar,
//         appBarTheme: const AppBarTheme(
//           backgroundColor: tealButtonAppbar,
//           iconTheme: IconThemeData(color: Colors.white),
//           titleTextStyle: TextStyle(
//               color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20),
//         ),
//       ),
//       home: VideoUploader(onToggleTheme: _toggleTheme, themeMode: _themeMode),
//     );
//   }
// }
//
// class VideoUploader extends StatefulWidget {
//   final VoidCallback onToggleTheme;
//   final ThemeMode themeMode;
//
//   const VideoUploader(
//       {super.key, required this.onToggleTheme, required this.themeMode});
//
//   @override
//   State<VideoUploader> createState() => _VideoUploaderState();
// }
//
// class _VideoUploaderState extends State<VideoUploader> {
//   File? _pickedMedia;
//   VideoPlayerController? _controller;
//   final ImagePicker picker = ImagePicker();
//   double _confidence = 50;
//
//   Future<void> _pickFromGallery() async {
//     final pickedFile = await picker.pickVideo(source: ImageSource.gallery);
//     if (pickedFile != null) {
//       await _handleMedia(File(pickedFile.path));
//     }
//   }
//
//   Future<void> _captureFromCamera() async {
//     final XFile? capturedFile =
//     await picker.pickVideo(source: ImageSource.camera);
//     if (capturedFile != null) {
//       await _handleMedia(File(capturedFile.path));
//     }
//   }
//
//   Future<void> _handleMedia(File file) async {
//     setState(() {
//       _pickedMedia = file;
//     });
//
//     final request = http.MultipartRequest(
//       'POST',
//       Uri.parse('http://172.18.40.127:8000/detect'),
//     );
//
//     request.files.add(await http.MultipartFile.fromPath('file', file.path));
//     request.fields['confidence_score'] = (_confidence / 100).toStringAsFixed(2);
//
//     try {
//       final response = await request.send();
//       developer.log(response.toString(), name: "Video");
//
//       if (response.statusCode == 200) {
//         Uint8List bytes = await response.stream.toBytes();
//         final tempDir = await getTemporaryDirectory();
//         final processedFile = File('${tempDir.path}/output.mp4');
//         await processedFile.writeAsBytes(bytes);
//         _controller?.dispose();
//         _controller = VideoPlayerController.file(processedFile)
//           ..initialize().then((_) {
//             setState(() {
//               _pickedMedia = processedFile;
//
//             });
//           });
//       } else {
//         // setState(() => _loading = false);
//         ScaffoldMessenger.of(context).showSnackBar(
//           SnackBar(content: Text('Server Error: ${response.statusCode}')),
//         );
//       }
//     } catch (e) {
//       // setState(() => _loading = false);
//       ScaffoldMessenger.of(context).showSnackBar(
//         SnackBar(content: Text('Upload failed: $e')),
//       );
//     }
//   }
//
//   void _showMediaOptions() {
//     showDialog(
//       context: context,
//       builder: (context) => Dialog(
//         shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
//         child: Container(
//           color: Colors.black,
//           padding: const EdgeInsets.all(20),
//           child: Column(
//             mainAxisSize: MainAxisSize.min,
//             children: [
//               const Text(
//                 'Select Media',
//                 style: TextStyle(
//                     fontWeight: FontWeight.bold,
//                     fontSize: 18,
//                     color: Colors.white),
//               ),
//               const SizedBox(height: 20),
//               ElevatedButton.icon(
//                 onPressed: () {
//                   Navigator.pop(context);
//                   _pickFromGallery();
//                 },
//                 icon: const Icon(Icons.photo),
//                 label: const Text('Gallery'),
//                 style: ElevatedButton.styleFrom(
//                   backgroundColor: tealButtonAppbar,
//                   foregroundColor: Colors.white,
//                   minimumSize: const Size.fromHeight(45),
//                   shape: RoundedRectangleBorder(
//                       borderRadius: BorderRadius.circular(4)),
//                 ),
//               ),
//               const SizedBox(height: 10),
//               ElevatedButton.icon(
//                 onPressed: () {
//                   Navigator.pop(context);
//                   _captureFromCamera();
//                 },
//                 icon: const Icon(Icons.camera_alt),
//                 label: const Text('Camera'),
//                 style: ElevatedButton.styleFrom(
//                   backgroundColor: tealButtonAppbar,
//                   foregroundColor: Colors.white,
//                   minimumSize: const Size.fromHeight(45),
//                   shape: RoundedRectangleBorder(
//                       borderRadius: BorderRadius.circular(4)),
//                 ),
//               ),
//             ],
//           ),
//         ),
//       ),
//     );
//   }
//
//   String _selectedOption = 'Object Detection';
//   bool _showControls = false;
//   Timer? _hideTimer;
//
//   Widget _mediaWidget() {
//     if (_controller == null || !_controller!.value.isInitialized) {
//       return const Padding(
//         padding: EdgeInsets.symmetric(vertical: 20),
//         child: Text(
//           'Processed media will appear here.',
//           style: TextStyle(color: Colors.white, fontSize: 16),
//         ),
//       );
//     }
//
//     final videoSize = _controller!.value.size;
//
//     return GestureDetector(
//       onTap: () {
//         setState(() => _showControls = !_showControls);
//         if (_showControls) {
//           _startHideTimer();
//         } else {
//           _hideTimer?.cancel();
//         }
//       },
//       child: Container(
//         decoration: BoxDecoration(
//           border: Border.all(color: Colors.white, width: 2),
//           borderRadius: BorderRadius.circular(8),
//         ),
//         padding: const EdgeInsets.all(8),
//         child: Stack(
//           alignment: Alignment.center,
//           children: [
//             FittedBox(
//               fit: BoxFit.contain,
//               child: SizedBox(
//                 width: videoSize.width,
//                 height: videoSize.height,
//                 child: VideoPlayer(_controller!),
//               ),
//             ),
//             if (_showControls) ...[
//               IconButton(
//                 iconSize: 64,
//                 icon: Icon(
//                   _controller!.value.isPlaying
//                       ? Icons.pause_circle
//                       : Icons.play_circle,
//                   color: Colors.white,
//                 ),
//                 onPressed: () {
//                   setState(() {
//                     _controller!.value.isPlaying
//                         ? _controller!.pause()
//                         : _controller!.play();
//                   });
//                   _startHideTimer();
//                 },
//               ),
//               Positioned(
//                 bottom: 0,
//                 left: 0,
//                 right: 0,
//                 child: Row(
//                   children: [
//                     Expanded(
//                       child: ValueListenableBuilder(
//                         valueListenable: _controller!,
//                         builder: (context, VideoPlayerValue value, child) {
//                           final duration = value.duration.inMilliseconds;
//                           final position = value.position.inMilliseconds;
//
//                           return Slider(
//                             value: position
//                                 .toDouble()
//                                 .clamp(0, duration.toDouble()),
//                             min: 0,
//                             max: duration.toDouble(),
//                             activeColor: tealButtonAppbar,
//                             inactiveColor: Colors.grey,
//                             onChanged: (newValue) {
//                               _controller!.seekTo(
//                                   Duration(milliseconds: newValue.toInt()));
//                               _startHideTimer();
//                             },
//                             onChangeStart: (_) => _hideTimer?.cancel(),
//                             onChangeEnd: (_) => _startHideTimer(),
//                           );
//                         },
//                       ),
//                     ),
//                     IconButton(
//                       icon: const Icon(Icons.fullscreen, color: Colors.white),
//                       onPressed: () {
//                         Navigator.push(
//                           context,
//                           MaterialPageRoute(
//                             builder: (_) =>
//                                 FullscreenVideoPage(controller: _controller!),
//                           ),
//                         );
//                       },
//                     ),
//                   ],
//                 ),
//               ),
//             ],
//           ],
//         ),
//       ),
//     );
//   }
//
//   void _startHideTimer() {
//     _hideTimer?.cancel();
//     _hideTimer = Timer(const Duration(seconds: 3), () {
//       setState(() => _showControls = false);
//     });
//   }
//
//   @override
//   void dispose() {
//     _controller?.dispose();
//     _hideTimer?.cancel();
//     super.dispose();
//   }
//
//   @override
//   Widget build(BuildContext context) {
//     bool isDark = widget.themeMode == ThemeMode.dark;
//
//     return Scaffold(
//       appBar: AppBar(
//         title: const Text('Pikachoo'),
//         actions: [
//           IconButton(
//             icon: Icon(
//               isDark ? Icons.wb_sunny : Icons.nightlight_round,
//               color: Colors.white,
//             ),
//             onPressed: widget.onToggleTheme,
//             tooltip: isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode',
//           ),
//         ],
//       ),
//       body: Stack(
//         children: [
//           SingleChildScrollView(
//             child: Column(
//               children: [
//                 const SizedBox(height: 16),
//                 Center(child: _mediaWidget()),
//                 const SizedBox(height: 10),
//                 SingleChildScrollView(
//                   scrollDirection: Axis.horizontal,
//                   padding: const EdgeInsets.symmetric(horizontal: 8),
//                   child: Row(
//                     children: [
//                       _buildOptionButton('Object Detection'),
//                       _buildOptionButton('Object Tracking'),
//                       _buildOptionButton('Stampede Detection'),
//                       _buildOptionButton('More1'),
//                       _buildOptionButton('More2'),
//                     ],
//                   ),
//                 ),
//                 const SizedBox(height: 20),
//                 Slider(
//                   value: _confidence,
//                   min: 0,
//                   max: 100,
//                   divisions: 100,
//                   activeColor: tealButtonAppbar,
//                   label: '${_confidence.toStringAsFixed(0)}%',
//                   onChanged: (value) {
//                     setState(() {
//                       _confidence = value;
//                     });
//                   },
//                 ),
//                 Text('Confidence: ${_confidence.toStringAsFixed(0)}%',
//                     style: const TextStyle(color: Colors.white)),
//                 const SizedBox(height: 30),
//               ],
//             ),
//           ),
//           // if (_loading)
//           //   Container(
//           //     color: Colors.black.withOpacity(0.7),
//           //     child: const Center(
//           //       child: CircularProgressIndicator(
//           //         color: Colors.white,
//           //         strokeWidth: 4,
//           //       ),
//           //     ),
//           //   ),
//         ],
//       ),
//       bottomNavigationBar: Padding(
//         padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
//         child: ElevatedButton.icon(
//           onPressed: _showMediaOptions,
//           icon: const Icon(Icons.upload_file),
//           label: const Text('Upload'),
//           style: ElevatedButton.styleFrom(
//             minimumSize: const Size.fromHeight(50),
//             backgroundColor: tealButtonAppbar,
//             foregroundColor: Colors.white,
//             shape:
//             RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
//           ),
//         ),
//       ),
//     );
//   }
//
//   Widget _buildOptionButton(String label) {
//     final isSelected = label == _selectedOption;
//     return Padding(
//       padding: const EdgeInsets.only(right: 8),
//       child: OutlinedButton(
//         onPressed: () {
//           setState(() => _selectedOption = label);
//           ScaffoldMessenger.of(context).showSnackBar(
//             SnackBar(content: Text('$label selected')),
//           );
//         },
//         style: OutlinedButton.styleFrom(
//           side: BorderSide(color: tealButtonAppbar),
//           backgroundColor: isSelected ? tealButtonAppbar : Colors.transparent,
//           foregroundColor: Colors.white,
//           padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
//           shape: RoundedRectangleBorder(
//             borderRadius: BorderRadius.circular(6),
//           ),
//         ),
//         child: Text(label),
//       ),
//     );
//   }
// }
//
// class FullscreenVideoPage extends StatefulWidget {
//   final VideoPlayerController controller;
//   const FullscreenVideoPage({super.key, required this.controller});
//   @override
//   State<FullscreenVideoPage> createState() => _FullscreenVideoPageState();
// }
//
// class _FullscreenVideoPageState extends State<FullscreenVideoPage> {
//   bool _showControls = true;
//   Timer? _hideTimer;
//
//   @override
//   void initState() {
//     super.initState();
//     _startHideTimer();
//   }
//
//   void _startHideTimer() {
//     _hideTimer?.cancel();
//     _hideTimer = Timer(const Duration(seconds: 3), () {
//       setState(() => _showControls = false);
//     });
//   }
//
//   @override
//   void dispose() {
//     _hideTimer?.cancel();
//     super.dispose();
//   }
//
//   @override
//   Widget build(BuildContext context) {
//     final controller = widget.controller;
//     return Scaffold(
//       backgroundColor: Colors.black,
//       body: GestureDetector(
//         onTap: () {
//           setState(() => _showControls = !_showControls);
//           if (_showControls) {
//             _startHideTimer();
//           } else {
//             _hideTimer?.cancel();
//           }
//         },
//         child: Stack(
//           alignment: Alignment.center,
//           children: [
//             Center(
//               child: AspectRatio(
//                 aspectRatio: controller.value.aspectRatio,
//                 child: VideoPlayer(controller),
//               ),
//             ),
//             if (_showControls) ...[
//               IconButton(
//                 iconSize: 64,
//                 icon: Icon(
//                   controller.value.isPlaying
//                       ? Icons.pause_circle
//                       : Icons.play_circle,
//                   color: Colors.white,
//                 ),
//                 onPressed: () {
//                   setState(() {
//                     controller.value.isPlaying
//                         ? controller.pause()
//                         : controller.play();
//                   });
//                   _startHideTimer();
//                 },
//               ),
//               Positioned(
//                 bottom: 0,
//                 left: 0,
//                 right: 0,
//                 child: Row(
//                   children: [
//                     Expanded(
//                       child: ValueListenableBuilder(
//                         valueListenable: controller,
//                         builder: (context, VideoPlayerValue value, child) {
//                           final duration = value.duration.inMilliseconds;
//                           final position = value.position.inMilliseconds;
//                           return Slider(
//                             value: position
//                                 .toDouble()
//                                 .clamp(0, duration.toDouble()),
//                             min: 0,
//                             max: duration.toDouble(),
//                             activeColor: Colors.teal,
//                             inactiveColor: Colors.grey,
//                             onChanged: (newValue) {
//                               controller.seekTo(
//                                   Duration(milliseconds: newValue.toInt()));
//                               _startHideTimer();
//                             },
//                             onChangeStart: (_) => _hideTimer?.cancel(),
//                             onChangeEnd: (_) => _startHideTimer(),
//                           );
//                         },
//                       ),
//                     ),
//                     IconButton(
//                       icon:
//                       const Icon(Icons.close_fullscreen, color: Colors.white),
//                       onPressed: () => Navigator.pop(context),
//                     ),
//                   ],
//                 ),
//               ),
//             ],
//           ],
//         ),
//       ),
//     );
//   }
// }

import 'dart:async';
import 'dart:io';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:video_player/video_player.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';

const Color darkBackground = Color(0xFF181818);
const Color tealButtonAppbar = Color(0xFF6F9F9C);

void main() => runApp(const PikachooApp());

class PikachooApp extends StatefulWidget {
  const PikachooApp({super.key});
  @override
  State<PikachooApp> createState() => _PikachooAppState();
}

class _PikachooAppState extends State<PikachooApp> {
  ThemeMode _themeMode = ThemeMode.dark;
  bool _proceeded = false;

  void _toggleTheme() {
    setState(() {
      _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    });
  }

  void _handleProceed() {
    setState(() {
      _proceeded = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      themeMode: _themeMode,
      theme: ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: Colors.white,
        primaryColor: tealButtonAppbar,
        appBarTheme: const AppBarTheme(
          backgroundColor: tealButtonAppbar,
          iconTheme: IconThemeData(color: Colors.white),
          titleTextStyle: TextStyle(
              color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20),
        ),
      ),
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: darkBackground,
        primaryColor: tealButtonAppbar,
        appBarTheme: const AppBarTheme(
          backgroundColor: tealButtonAppbar,
          iconTheme: IconThemeData(color: Colors.white),
          titleTextStyle: TextStyle(
              color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20),
        ),
      ),
      home: _proceeded
          ? VideoUploader(onToggleTheme: _toggleTheme, themeMode: _themeMode)
          : SplashScreen(onProceed: _handleProceed),
    );
  }
}


class VideoUploader extends StatefulWidget {
  final VoidCallback onToggleTheme;

  final ThemeMode themeMode;

  const VideoUploader(
      {super.key, required this.onToggleTheme, required this.themeMode});

  @override
  State<VideoUploader> createState() => _VideoUploaderState();
}

class _VideoUploaderState extends State<VideoUploader> {
  bool _isOverlay = true;
  File? _pickedMedia;
  VideoPlayerController? _controller;
  final ImagePicker picker = ImagePicker();
  double _confidence = 50;
  bool _loading = false;

  Future<void> _pickFromGallery() async {
    final pickedFile = await picker.pickVideo(source: ImageSource.gallery);
    if (pickedFile != null) {
      await _handleMedia(File(pickedFile.path`));
    }
  }

  Future<void> _captureFromCamera() async {
    final XFile? capturedFile =
    await picker.pickVideo(source: ImageSource.camera);
    if (capturedFile != null) {
      await _handleMedia(File(capturedFile.path));
    }
  }
  String? _stampedeStatus;
  Future<void> _handleMedia(File file) async {
    setState(() {
      _pickedMedia = file;
      _loading = true;
    });

    String endpoint;
    if (_selectedOption == 'Object Detection') {
      endpoint = '/detect';
    } else if (_selectedOption == 'Object Tracking') {
      endpoint = '/track';
    } else if(_selectedOption == 'Anomaly Detection'){
      endpoint = '/anam';
    } else if(_selectedOption == 'Velocity Map'){
      endpoint = '/vmap';
    }
    else {
      endpoint = '/nnn';
    }

    final request = http.MultipartRequest(
      'POST',
      Uri.parse('http://172.18.40.127:8000$endpoint'),
    );

    request.files.add(await http.MultipartFile.fromPath('file', file.path));

    // Fix field names to match FastAPI
    request.fields['confidence'] = (_confidence / 100).toStringAsFixed(2);
    if (_selectedOption == 'Object Tracking') {
      request.fields['overlay'] = _isOverlay.toString();  // e.g. "true"
    }

    try {
      final response = await request.send();
      if (response.statusCode == 200) {
        final isStampede = await response.headers['x-is-stampede'];
        setState(() {
          print('Response Headers:');
          response.headers.forEach((key, value) {
            print('$key: $value');
          });
          _stampedeStatus = (isStampede == 'true') ? 'true' : 'false';
        });
        final bytes = await response.stream.toBytes();
        final tempDir = await getTemporaryDirectory();
        final processedFile = File('${tempDir.path}/output.mp4');
        await processedFile.writeAsBytes(bytes);

        _controller?.dispose();
        _controller = VideoPlayerController.file(processedFile)
          ..initialize().then((_) {
            setState(() {
              _pickedMedia = processedFile;
              _loading = false;
            });
            _controller?.play();
          });
      } else {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Server Error: ${response.statusCode}')),
        );
      }
    } catch (e) {
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Upload failed: $e')),
      );
    }
  }

  void _showMediaOptions() {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        child: Container(
          width: MediaQuery.of(context).size.width * 0.85, // make it wider
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 30),
          decoration: BoxDecoration(
            color: Colors.black,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Select Media',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 20,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 25),
              ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  _pickFromGallery();
                },
                icon: const Icon(Icons.photo),
                label: const Text('Gallery'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.tealAccent,
                  foregroundColor: Colors.black,
                  minimumSize: const Size.fromHeight(50),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(6),
                  ),
                ),
              ),
              const SizedBox(height: 15),
              ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  _captureFromCamera();
                },
                icon: const Icon(Icons.camera_alt),
                label: const Text('Camera'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.tealAccent,
                  foregroundColor: Colors.black,
                  minimumSize: const Size.fromHeight(50),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(6),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _downloadVideo() async {
    if (_pickedMedia == null) return;

    // Request permission
    final status = await Permission.storage.request();
    if (!status.isGranted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Storage permission is required')),
      );
      return;
    }

    final downloadsDir = Directory('/storage/emulated/0/Download');
    final fileName = 'processed_video_${DateTime.now().millisecondsSinceEpoch}.mp4';
    final savedFile = File('${downloadsDir.path}/$fileName');

    try {
      await savedFile.writeAsBytes(await _pickedMedia!.readAsBytes());
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Video saved to Downloads as $fileName')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to save video: $e')),
      );
    }
  }


  String _selectedOption = 'Object Detection';
  bool _showControls = false;
  Timer? _hideTimer;

  // Widget _mediaWidget() {
  //   if (_controller == null || !_controller!.value.isInitialized) {
  //     return const Padding(
  //       padding: EdgeInsets.symmetric(vertical: 20),
  //       child: Text(
  //         'Processed media will appear here.',
  //         style: TextStyle(color: Colors.white, fontSize: 16),
  //       ),
  //     );
  //   }
  //
  //   final videoSize = _controller!.value.size;
  //
  //   return GestureDetector(
  //     onTap: () {
  //       setState(() => _showControls = !_showControls);
  //       if (_showControls) {
  //         _startHideTimer();
  //       } else {
  //         _hideTimer?.cancel();
  //       }
  //     },
  //     child: Container(
  //       decoration: BoxDecoration(
  //         border: Border.all(color: Colors.white, width: 2),
  //         borderRadius: BorderRadius.circular(8),
  //       ),
  //       padding: const EdgeInsets.all(8),
  //       child: Stack(
  //         alignment: Alignment.center,
  //         children: [
  //           FittedBox(
  //             fit: BoxFit.contain,
  //             child: SizedBox(
  //               width: videoSize.width,
  //               height: videoSize.height,
  //               child: VideoPlayer(_controller!),
  //             ),
  //           ),
  //           if (_showControls) ...[
  //             Positioned(
  //               top: 10,
  //               right: 10,
  //               child: IconButton(
  //                 icon: const Icon(Icons.download, color: Colors.white),
  //                 tooltip: 'Download',
  //                 onPressed: _downloadVideo,
  //               ),
  //             ),
  //             IconButton(
  //               iconSize: 64,
  //               icon: Icon(
  //                 _controller!.value.isPlaying
  //                     ? Icons.pause_circle
  //                     : Icons.play_circle,
  //                 color: Colors.white,
  //               ),
  //               onPressed: () {
  //                 setState(() {
  //                   _controller!.value.isPlaying
  //                       ? _controller!.pause()
  //                       : _controller!.play();
  //                 });
  //                 _startHideTimer();
  //               },
  //             ),
  //             Positioned(
  //               bottom: 0,
  //               left: 0,
  //               right: 0,
  //               child: Row(
  //                 children: [
  //                   Expanded(
  //                     child: ValueListenableBuilder(
  //                       valueListenable: _controller!,
  //                       builder: (context, VideoPlayerValue value, child) {
  //                         final duration = value.duration.inMilliseconds;
  //                         final position = value.position.inMilliseconds;
  //
  //                         return Slider(
  //                           value: position.toDouble().clamp(0, duration.toDouble()),
  //                           min: 0,
  //                           max: duration.toDouble(),
  //                           activeColor: tealButtonAppbar,
  //                           inactiveColor: Colors.grey,
  //                           onChanged: (newValue) {
  //                             _controller!.seekTo(
  //                               Duration(milliseconds: newValue.toInt()),
  //                             );
  //                             _startHideTimer();
  //                           },
  //                           onChangeStart: (_) => _hideTimer?.cancel(),
  //                           onChangeEnd: (_) => _startHideTimer(),
  //                         );
  //                       },
  //                     ),
  //                   ),
  //                   IconButton(
  //                     icon: const Icon(Icons.fullscreen, color: Colors.white),
  //                     onPressed: () {
  //                       Navigator.push(
  //                         context,
  //                         MaterialPageRoute(
  //                           builder: (_) => FullscreenVideoPage(controller: _controller!),
  //                         ),
  //                       );
  //                     },
  //                   ),
  //                   if (_stampedeStatus == 'true')
  //                     Padding(
  //                       padding: const EdgeInsets.symmetric(vertical: 8),
  //                       child: Text(
  //                         'STAMPEDE DETECTED, ALERT SENT',
  //                         style: TextStyle(
  //                           color: Colors.red,
  //                           fontWeight: FontWeight.bold,
  //                           fontSize: 18,
  //                         ),
  //                       ),
  //                     ),
  //                   if (_stampedeStatus == 'false')
  //                     Padding(
  //                       padding: const EdgeInsets.symmetric(vertical: 8),
  //                       child: Text(
  //                           'STAMPEDE DETECTED, ALERT SENT',
  //                           style: TextStyle(
  //                           color: Colors.red,
  //                           fontWeight: FontWeight.bold,
  //                           fontSize: 18,
  //                         ),
  //                       ),
  //                     ),
  //                 ],
  //               ),
  //             ),
  //           ],
  //         ],
  //       ),
  //     ),
  //   );
  // }
  Widget _mediaWidget() {
    if (_controller == null || !_controller!.value.isInitialized) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 20),
        child: Text(
          'Processed media will appear here.',
          style: TextStyle(color: Colors.white, fontSize: 16),
        ),
      );
    }

    final videoSize = _controller!.value.size;

    return Column(
      children: [
        if (_stampedeStatus == 'true')
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Text(
              '⚠️ STAMPEDE DETECTED, ALERT SENT',
              style: const TextStyle(
                color: Colors.red,
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
              textAlign: TextAlign.center,
            ),
          ),
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: Colors.white, width: 2),
            borderRadius: BorderRadius.circular(8),
          ),
          padding: const EdgeInsets.all(8),
          child: GestureDetector(
            onTap: () {
              setState(() => _showControls = !_showControls);
              if (_showControls) {
                _startHideTimer();
              } else {
                _hideTimer?.cancel();
              }
            },
            child: Stack(
              alignment: Alignment.center,
              children: [
                FittedBox(
                  fit: BoxFit.contain,
                  child: SizedBox(
                    width: videoSize.width,
                    height: videoSize.height,
                    child: VideoPlayer(_controller!),
                  ),
                ),
                if (_showControls) ...[
                  Positioned(
                    top: 10,
                    right: 10,
                    child: IconButton(
                      icon: const Icon(Icons.download, color: Colors.white),
                      tooltip: 'Download',
                      onPressed: _downloadVideo,
                    ),
                  ),
                  IconButton(
                    iconSize: 64,
                    icon: Icon(
                      _controller!.value.isPlaying
                          ? Icons.pause_circle
                          : Icons.play_circle,
                      color: Colors.white,
                    ),
                    onPressed: () {
                      setState(() {
                        _controller!.value.isPlaying
                            ? _controller!.pause()
                            : _controller!.play();
                      });
                      _startHideTimer();
                    },
                  ),
                  Positioned(
                    bottom: 0,
                    left: 0,
                    right: 0,
                    child: Row(
                      children: [
                        Expanded(
                          child: ValueListenableBuilder(
                            valueListenable: _controller!,
                            builder: (context, VideoPlayerValue value, child) {
                              final duration = value.duration.inMilliseconds;
                              final position = value.position.inMilliseconds;

                              return Slider(
                                value: position.toDouble().clamp(0, duration.toDouble()),
                                min: 0,
                                max: duration.toDouble(),
                                activeColor: tealButtonAppbar,
                                inactiveColor: Colors.grey,
                                onChanged: (newValue) {
                                  _controller!.seekTo(
                                    Duration(milliseconds: newValue.toInt()),
                                  );
                                  _startHideTimer();
                                },
                                onChangeStart: (_) => _hideTimer?.cancel(),
                                onChangeEnd: (_) => _startHideTimer(),
                              );
                            },
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.fullscreen, color: Colors.white),
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) =>
                                    FullscreenVideoPage(controller: _controller!),
                              ),
                            );
                          },
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }

  void _showStampedeWarningDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFFFFF3CD), // Light warning yellow
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        title: Row(
          children: const [
            Icon(Icons.info_outline, color: Colors.black87),
            SizedBox(width: 8),
            Text(
              'Message',
              style: TextStyle(
                color: Colors.black87,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 40),
            SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Warning Modal',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'This is a Warning message modal.',
                    style: TextStyle(color: Colors.black87),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            style: TextButton.styleFrom(
              backgroundColor: Colors.orange.shade600,
              foregroundColor: Colors.white,
            ),
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Ok'),
          ),
        ],
      ),
    );
  }



  void _startHideTimer() {
    _hideTimer?.cancel();
    _hideTimer = Timer(const Duration(seconds: 3), () {
      setState(() => _showControls = false);
    });
  }

  @override
  void dispose() {
    _controller?.dispose();
    _hideTimer?.cancel();
    super.dispose();
  }
  @override
  Widget build(BuildContext context) {
    bool isDark = widget.themeMode == ThemeMode.dark;

    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(kToolbarHeight),
        child: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Colors.teal, Colors.tealAccent],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: AppBar(
            backgroundColor: Colors.transparent, // important!
            elevation: 0,
            title: const Text(
              'Pikachoo AI',
              style: TextStyle(
                color: Colors.black,
                fontWeight: FontWeight.bold,
                fontSize: 20,
                fontFamily: 'Roboto', // You can change this to any custom font you added
              ),
            ),
          ),
        ),
      ),
      body: Stack(
        children: [
          SingleChildScrollView(
            child: Column(
              children: [
                const SizedBox(height: 16),
                Center(child: _mediaWidget()),
                const SizedBox(height: 10),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    alignment: WrapAlignment.center,
                    children: [
                      _buildOptionButton('Object Detection'),
                      _buildOptionButton('Object Tracking'),
                      _buildOptionButton('Anomaly Detection'),
                      _buildOptionButton('Velocity Map'),
                    ],
                  ),
                ),

                const SizedBox(height: 20),

                // === Conditionally show confidence slider and overlay ===
                if (_selectedOption == 'Object Detection' ||
                    _selectedOption == 'Object Tracking' ||
                    _selectedOption == 'Anomaly Detection' ||
                    _selectedOption == 'Velocity Map'
                ) ...[
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start, // Align children to the left
                    children: [
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8.0), // spacing between text and slider
                        child: Padding(
                          padding: const EdgeInsets.only(left: 22.0, top: 22.0),
                          child: Text(
                            'Confidence: ${_confidence.toInt()}%', // Display integer percentage
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ),
                      SliderTheme(
                        data: SliderTheme.of(context).copyWith(
                          activeTrackColor: Colors.teal,
                          inactiveTrackColor: Colors.grey[600],
                          thumbColor: Colors.transparent,
                          overlayColor: Colors.teal.withOpacity(0.2),
                          trackHeight: 4,
                          thumbShape: _TransparentThumbWithBorder(),
                          overlayShape: const RoundSliderOverlayShape(overlayRadius: 20),
                        ),
                        child: Slider(
                          value: _confidence,
                          min: 0,
                          max: 100,
                          divisions: 100,
                          onChanged: (value) {
                            setState(() {
                              _confidence = value;
                            });
                          },
                        ),
                      ),
                    ],
                  ),
                ],

                if (_selectedOption == 'Object Tracking') ...[
                  const SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Checkbox(
                        value: _isOverlay,
                        onChanged: (value) {
                          setState(() {
                            _isOverlay = value!;
                          });
                        },
                        checkColor: Colors.white,
                        activeColor: tealButtonAppbar,
                      ),
                      const Text('Enable Overlay', style: TextStyle(color: Colors.white)),
                    ],
                  ),
                ],
                const SizedBox(height: 30),
              ],
            ),
          ),
          if (_loading)
            Container(
              color: Colors.black.withOpacity(0.7),
              child: Center(
                  child: TriangularMergeLoader()
              ),
            ),
        ],
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
        child: GradientCircleButton(
          onPressed: _showMediaOptions,
          icon: Icons.upload_file,
          label: 'Upload',
        ),
      ),
    );
  }


  Widget _buildOptionButton(String label) {
    final isSelected = label == _selectedOption;

    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: GestureDetector(
        onTap: () {
          setState(() => _selectedOption = label);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('$label selected')),
          );
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: isSelected
              ? const EdgeInsets.symmetric(horizontal: 18, vertical: 15)
              : const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            gradient: isSelected
                ? const LinearGradient(
              colors: [Colors.teal, Colors.tealAccent],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            )
                : null,
            color: isSelected ? null : Colors.transparent,
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: tealButtonAppbar),
          ),
          child: Text(
            label,
            style: TextStyle(
              fontSize: isSelected ? 15.5 : 14,
              fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              color: isSelected ? Colors.black : Colors.white, // Black text over gradient
            ),
          ),
        ),
      ),
    );
  }


}

class FullscreenVideoPage extends StatefulWidget {
  final VideoPlayerController controller;
  const FullscreenVideoPage({super.key, required this.controller});
  @override
  State<FullscreenVideoPage> createState() => _FullscreenVideoPageState();
}

class _FullscreenVideoPageState extends State<FullscreenVideoPage> {
  bool _showControls = true;
  Timer? _hideTimer;

  @override
  void initState() {
    super.initState();
    _startHideTimer();
  }

  void _startHideTimer() {
    _hideTimer?.cancel();
    _hideTimer = Timer(const Duration(seconds: 3), () {
      setState(() => _showControls = false);
    });
  }

  @override
  void dispose() {
    _hideTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;
    return Scaffold(
      backgroundColor: Colors.black,
      body: GestureDetector(
        onTap: () {
          setState(() => _showControls = !_showControls);
          if (_showControls) {
            _startHideTimer();
          } else {
            _hideTimer?.cancel();
          }
        },
        child: Stack(
          alignment: Alignment.center,
          children: [
            Center(
              child: AspectRatio(
                aspectRatio: controller.value.aspectRatio,
                child: VideoPlayer(controller),
              ),
            ),
            if (_showControls) ...[
              IconButton(
                iconSize: 64,
                icon: Icon(
                  controller.value.isPlaying
                      ? Icons.pause_circle
                      : Icons.play_circle,
                  color: Colors.white,
                ),
                onPressed: () {
                  setState(() {
                    controller.value.isPlaying
                        ? controller.pause()
                        : controller.play();
                  });
                  _startHideTimer();
                },
              ),
              Positioned(
                bottom: 0,
                left: 0,
                right: 0,
                child: Row(
                  children: [
                    Expanded(
                      child: ValueListenableBuilder(
                        valueListenable: controller,
                        builder: (context, VideoPlayerValue value, child) {
                          final duration = value.duration.inMilliseconds;
                          final position = value.position.inMilliseconds;
                          return Slider(
                            value: position
                                .toDouble()
                                .clamp(0, duration.toDouble()),
                            min: 0,
                            max: duration.toDouble(),
                            activeColor: Colors.teal,
                            inactiveColor: Colors.grey,
                            onChanged: (newValue) {
                              controller.seekTo(
                                  Duration(milliseconds: newValue.toInt()));
                              _startHideTimer();
                            },
                            onChangeStart: (_) => _hideTimer?.cancel(),
                            onChangeEnd: (_) => _startHideTimer(),
                          );
                        },
                      ),
                    ),
                    IconButton(
                      icon:
                      const Icon(Icons.close_fullscreen, color: Colors.white),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class TriangularMergeLoader extends StatefulWidget {
  final double size;
  final Color color;

  const TriangularMergeLoader({
    this.size = 100,
    this.color = Colors.teal,
    super.key,
  });

  @override
  State<TriangularMergeLoader> createState() => _TriangularMergeLoaderState();
}

class _TriangularMergeLoaderState extends State<TriangularMergeLoader> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _radiusAnimation;
  late final Animation<double> _rotationAnimation;

  @override
  void initState() {
    super.initState();

    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();

    _radiusAnimation = TweenSequence([
      TweenSequenceItem(tween: Tween(begin: 1.0, end: 0.0).chain(CurveTween(curve: Curves.easeInOut)), weight: 50),
      TweenSequenceItem(tween: Tween(begin: 0.0, end: 1.0).chain(CurveTween(curve: Curves.easeInOut)), weight: 50),
    ]).animate(_controller);

    _rotationAnimation = Tween(begin: 0.0, end: 2 * pi).animate(_controller);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Offset _calculateOffset(double angle, double radius) {
    return Offset(
      radius * cos(angle),
      radius * sin(angle),
    );
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          final double baseRadius = widget.size * 0.3 * _radiusAnimation.value;
          final List<Offset> positions = [
            _calculateOffset(_rotationAnimation.value, baseRadius),
            _calculateOffset(_rotationAnimation.value + 2 * pi / 3, baseRadius),
            _calculateOffset(_rotationAnimation.value + 4 * pi / 3, baseRadius),
          ];

          return Stack(
            alignment: Alignment.center,
            children: List.generate(3, (i) {
              return Transform.translate(
                offset: positions[i],
                child: Container(
                  width: widget.size * 0.15,
                  height: widget.size * 0.15,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: widget.color,
                  ),
                ),
              );
            }),
          );
        },
      ),
    );
  }
}

class _TransparentThumbWithBorder extends SliderComponentShape {
  const _TransparentThumbWithBorder();

  @override
  Size getPreferredSize(bool isEnabled, bool isDiscrete) => const Size(20, 20);

  @override
  void paint(
      PaintingContext context,
      Offset center, {
        required Animation<double> activationAnimation,
        required Animation<double> enableAnimation,
        required bool isDiscrete,
        required TextPainter labelPainter,
        required RenderBox parentBox,
        required SliderThemeData sliderTheme,
        required TextDirection textDirection,
        required double value,
        required double textScaleFactor,
        required Size sizeWithOverflow,
      }) {
    final Canvas canvas = context.canvas;

    // Move the circle upward by its radius (10 pixels)
    final Offset shiftedCenter = Offset(center.dx + 10, center.dy);

    final Paint paint = Paint()
      ..color = Colors.tealAccent
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;

    canvas.drawCircle(shiftedCenter, 10, paint);
  }
}



class GradientCircleButton extends StatefulWidget {
  final VoidCallback onPressed;
  final IconData? icon; // Make optional
  final String label;

  const GradientCircleButton({
    Key? key,
    required this.onPressed,
    this.icon,
    required this.label,
  }) : super(key: key);

  @override
  State<GradientCircleButton> createState() => _GradientCircleButtonState();
}

class _GradientCircleButtonState extends State<GradientCircleButton> {
  double _scale = 1.0;

  void _onTapDown(TapDownDetails _) => setState(() => _scale = 0.95);
  void _onTapUp(TapUpDetails _) {
    setState(() => _scale = 1.0);
    widget.onPressed();
  }

  void _onTapCancel() => setState(() => _scale = 1.0);

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: _onTapDown,
      onTapUp: _onTapUp,
      onTapCancel: _onTapCancel,
      child: AnimatedScale(
        scale: _scale,
        duration: const Duration(milliseconds: 100),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Colors.teal, Colors.tealAccent],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(30),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.2),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.max,
            children: [
              if (widget.icon != null) ...[
                Icon(widget.icon, color: Colors.black),
                const SizedBox(width: 8),
              ],
              Text(
                widget.label,
                style: const TextStyle(
                  color: Colors.black,
                  fontWeight: FontWeight.bold,
                  fontSize: 16, // Slightly bigger
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}



class SplashScreen extends StatelessWidget {
  final VoidCallback onProceed;
  static const Color darkBackground = Color(0xFF181818);

  const SplashScreen({super.key, required this.onProceed});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: darkBackground,
      body: SafeArea(
        child: Stack(
          children: [
            Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ShaderMask(
                    shaderCallback: (Rect bounds) {
                      return const LinearGradient(
                        colors: [Colors.teal, Colors.white], // Gradient from teal to white
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ).createShader(bounds);
                    },
                    child: const Text(
                      'Welcome to',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 30,
                        fontWeight: FontWeight.bold,
                        color: Colors.white, // Fallback color (will not be used since the shader is applied)
                        height: 2,
                      ),
                    ),
                  ),
      ShaderMask(
        shaderCallback: (Rect bounds) {
          return const LinearGradient(
            colors: [Colors.teal, Colors.white],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ).createShader(bounds);
        },
        blendMode: BlendMode.srcIn,
        child: ReversibleTypewriter(
          text: 'Pikachoo AI..',
          style: const TextStyle(
            fontSize: 52,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
                ],
              ),
            ),
            Positioned(
              bottom: 30,
              left: 20,
              right: 20,
              child: GestureDetector(
                onTap: onProceed,
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Colors.teal, Colors.tealAccent],
                      begin: Alignment.centerLeft,
                      end: Alignment.centerRight,
                    ),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Center(
                    child: Text(
                      'Proceed',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class ReversibleTypewriter extends StatefulWidget {
  final String text;
  final TextStyle style;
  final Duration speed;
  final Duration pause;
  const ReversibleTypewriter({
    super.key,
    required this.text,
    required this.style,
    this.speed = const Duration(milliseconds: 150),
    this.pause = const Duration(milliseconds: 700),
  });

  @override
  State<ReversibleTypewriter> createState() => _ReversibleTypewriterState();
}

class _ReversibleTypewriterState extends State<ReversibleTypewriter> {
  late Timer _timer;
  int _index = 0;
  bool _isForward = true;

  @override
  void initState() {
    super.initState();
    _startTyping();
  }

  void _startTyping() {
    _timer = Timer.periodic(widget.speed, (timer) {
      setState(() {
        if (_isForward) {
          _index++;
          if (_index == widget.text.length) {
            _isForward = false;
            _pause();
          }
        } else {
          _index--;
          if (_index == 0) {
            _isForward = true;
            _pause();
          }
        }
      });
    });
  }

  void _pause() {
    _timer.cancel();
    Future.delayed(widget.pause, () {
      _startTyping();
    });
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Text(
      widget.text.substring(0, _index),
      style: widget.style,
    );
  }
}