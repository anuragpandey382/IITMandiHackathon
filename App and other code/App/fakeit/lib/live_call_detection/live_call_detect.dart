import 'dart:async';
import 'dart:io';
import 'package:fakeit/config/secreats.dart';
import 'package:flutter/material.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:playback_capture/data/config/audioencoding.dart';
import 'package:playback_capture/data/playback_capture_result.dart';
import 'package:playback_capture/playback_capture.dart';

class LiveCallDetect extends StatefulWidget {
  const LiveCallDetect({super.key});

  @override
  State<LiveCallDetect> createState() => _LiveCallDetectState();
}

class _LiveCallDetectState extends State<LiveCallDetect> {
  final RTCVideoRenderer localVideo = RTCVideoRenderer();
  final RTCVideoRenderer remoteVideo = RTCVideoRenderer();
  late final MediaStream localStream;
  late final WebSocketChannel channel;
  MediaStream? remoteStream;
  RTCPeerConnection? peerConnection;
  MediaStreamTrack? remoteAudioTrack;
  List<String> filesListForPrediction = [];
  String pridiction = "";

  final List<Uint8List> _pcmChunks = [];

  _predictWav() async {
    if (filesListForPrediction.isNotEmpty) {
      String filePath = filesListForPrediction[0];
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('http://${Secreat.server}/cgi-bin/predict1.py'),
      );
      request.files.add(
        await http.MultipartFile.fromPath('audio_file', '${filePath}'),
      );

      http.StreamedResponse response = await request.send();

      if (response.statusCode == 200) {
        String res = await response.stream.bytesToString();
        print("Response: $res");
        pridiction = json.decode(res)["prediction"].toString();
      } else {
        print(response.reasonPhrase);
      }

      filesListForPrediction.removeAt(0);
    }
  }

  getPermission() async {
    final status = await Permission.storage.status;

    // 2. If not granted, request it
    if (!status.isGranted) {
      print('Permission is  to save file path');
      final result = await Permission.storage.request();

      if (!result.isGranted) {
        print('Permission is  to save file denied ');
        // User denied permission—handle gracefully\
        await Permission.storage.request();
        throw Exception('Storage permission denied');
      }
    }
  }

  _startRecording() {
    _recorder?.cancel();
    _recorder = Timer.periodic(Duration(seconds: 2), (_timer) async {
      _pcmChunks.clear();
      final PlaybackCaptureResult playbackCaptureResult =
          await _playbackCapturePlugin.listenAudio(
            encoding: AudioEncoding.pcm16,
            sampleRate: 16000,
            audioDataCallback: (Uint8List data) {
              _pcmChunks.add(data);
              setState(() {
                _readTotal += data.length;
              });
            },
          );
      if (playbackCaptureResult != PlaybackCaptureResult.recording) {
        if (playbackCaptureResult ==
            PlaybackCaptureResult.missingAudioRecordPermission) {
          await Permission.microphone.request();
        } else if (playbackCaptureResult ==
            PlaybackCaptureResult.recordRequestDenied) {
          // TODO: User denied capturing
        }
      } else {
        setState(() {
          _capturing = true;
        });
      }
      Timer(Duration(seconds: 1), () async {
        await _playbackCapturePlugin.stopListening();
        setState(() {
          _capturing = false;
        });

        // Save to app documents
        List<int> recordedData = [];
        List<int> allBytes = _pcmChunks.expand((chunk) => chunk).toList();
        recordedData.addAll(allBytes);
        final dir = await getApplicationDocumentsDirectory();
        final path =
            '${dir.path}/remote_audio_${DateTime.now().millisecondsSinceEpoch}.wav';
        print('Try to save file $path');
        saveFileInWave(recordedData, 16000, path);
        filesListForPrediction.add(path);
        print('WAV saved to $path');
        _predictWav();
      });
    });
  }

  Future<void> saveFileInWave(
    List<int> data,
    int sampleRate,
    String path,
  ) async {
    File recordedFile = File(path);

    var channels = 1;

    int byteRate = ((16 * sampleRate * channels) / 8).round();

    var size = data.length;

    var fileSize = size + 36;

    Uint8List header = Uint8List.fromList([
      // "RIFF"
      82, 73, 70, 70,
      fileSize & 0xff,
      (fileSize >> 8) & 0xff,
      (fileSize >> 16) & 0xff,
      (fileSize >> 24) & 0xff,
      // WAVE
      87, 65, 86, 69,
      // fmt
      102, 109, 116, 32,
      // fmt chunk size 16
      16, 0, 0, 0,
      // Type of format
      1, 0,
      // One channel
      channels, 0,
      // Sample rate
      sampleRate & 0xff,
      (sampleRate >> 8) & 0xff,
      (sampleRate >> 16) & 0xff,
      (sampleRate >> 24) & 0xff,
      // Byte rate
      byteRate & 0xff,
      (byteRate >> 8) & 0xff,
      (byteRate >> 16) & 0xff,
      (byteRate >> 24) & 0xff,
      // Uhm
      ((16 * channels) / 8).round(), 0,
      // bitsize
      16, 0,
      // "data"
      100, 97, 116, 97,
      size & 0xff,
      (size >> 8) & 0xff,
      (size >> 16) & 0xff,
      (size >> 24) & 0xff,
      ...data,
    ]);
    return recordedFile.writeAsBytesSync(header, flush: true);
  }

  /* Recording */
  Timer? _recorder;
  final _playbackCapturePlugin = PlaybackCapture();
  int _readTotal = 0;
  bool _capturing = false;

  // Connecting with websocket Server
  void connectToServer() {
    try {
      channel = WebSocketChannel.connect(
        Uri.parse("ws://${Secreat.server}:8080"),
      );

      // Listening to the socket event as a stream
      channel.stream.listen((message) async {
        // Decoding message
        Map<String, dynamic> decoded = jsonDecode(message);

        // If the client receive an offer
        if (decoded["event"] == "offer") {
          // Set the offer SDP to remote description
          await peerConnection?.setRemoteDescription(
            RTCSessionDescription(
              decoded["data"]["sdp"],
              decoded["data"]["type"],
            ),
          );

          // Create an answer
          RTCSessionDescription answer = await peerConnection!.createAnswer();

          // Set the answer as an local description
          await peerConnection!.setLocalDescription(answer);

          // Send the answer to the other peer
          channel.sink.add(
            jsonEncode({"event": "answer", "data": answer.toMap()}),
          );
        }
        // If client receive an Ice candidate from the peer
        else if (decoded["event"] == "ice") {
          // It add to the RTC peer connection
          peerConnection?.addCandidate(
            RTCIceCandidate(
              decoded["data"]["candidate"],
              decoded["data"]["sdpMid"],
              decoded["data"]["sdpMLineIndex"],
            ),
          );
        }
        // If Client recive an reply of their offer as answer
        else if (decoded["event"] == "answer") {
          await peerConnection?.setRemoteDescription(
            RTCSessionDescription(
              decoded["data"]["sdp"],
              decoded["data"]["type"],
            ),
          );
        }
        // If no condition fulfilled? printout the message
        else {
          print(decoded);
        }
      });
    } catch (e) {
      throw "ERROR $e";
    }
  }

  // STUN server configuration
  Map<String, dynamic> configuration = {
    'iceServers': [
      {
        'urls': [
          'stun:stun1.l.google.com:19302',
          'stun:stun2.l.google.com:19302',
        ],
      },
    ],
  };

  // This must be done as soon as app loads
  void initialization() async {
    // Getting video feed from the user camera
    localStream = await navigator.mediaDevices.getUserMedia({
      'video': true,
      'audio': true,
    });

    // Set the local video to display
    localVideo.srcObject = localStream;
    // Initializing the peer connecion
    peerConnection = await createPeerConnection(configuration);
    setState(() {});
    // Adding the local media to peer connection
    // When connection establish, it send to the remote peer
    localStream.getTracks().forEach((track) {
      peerConnection?.addTrack(track, localStream);
    });
  }

  void makeCall() async {
    // Creating a offer for remote peer
    RTCSessionDescription offer = await peerConnection!.createOffer();

    // Setting own SDP as local description
    await peerConnection?.setLocalDescription(offer);

    // Sending the offer
    channel.sink.add(jsonEncode({"event": "offer", "data": offer.toMap()}));
  }

  // Help to debug our code
  void registerPeerConnectionListeners() {
    peerConnection?.onIceGatheringState = (RTCIceGatheringState state) {
      print('ICE gathering state changed: $state');
    };

    peerConnection?.onIceCandidate = (RTCIceCandidate candidate) {
      channel.sink.add(jsonEncode({"event": "ice", "data": candidate.toMap()}));
    };

    peerConnection?.onConnectionState = (RTCPeerConnectionState state) {
      print('Connection state change: $state');
    };

    peerConnection?.onSignalingState = (RTCSignalingState state) {
      print('Signaling state change: $state');
    };

    peerConnection?.onTrack = ((tracks) {
      tracks.streams[0].getTracks().forEach((track) {
        remoteStream?.addTrack(track);
      });
    });

    // When stream is added from the remote peer
    peerConnection?.onAddStream = (MediaStream stream) {
      remoteVideo.srcObject = stream;
      remoteAudioTrack = stream.getAudioTracks().firstWhere(
        (t) => t.kind == 'audio',
      );
      setState(() {});
      setState(() {});
    };
  }

  @override
  void initState() {
    getPermission();
    connectToServer();
    localVideo.initialize();
    remoteVideo.initialize();
    initialization();
    _startRecording();
    super.initState();
  }

  @override
  void dispose() {
    peerConnection?.close();
    localVideo.dispose();
    remoteVideo.dispose();
    _playbackCapturePlugin.stopListening();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Flutter webrtc websocket")),
      body: Stack(
        children: [
          SizedBox(
            height: MediaQuery.of(context).size.height,
            width: MediaQuery.of(context).size.width,
            child: RTCVideoView(remoteVideo, mirror: false),
          ),
          Positioned(
            right: 10,
            child: SizedBox(
              height: 200,
              width: 200,
              child: RTCVideoView(localVideo, mirror: true),
            ),
          ),
          Positioned(top: 20, child: Text(pridiction)),
        ],
      ),
      floatingActionButton: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          FloatingActionButton(
            backgroundColor: Colors.amberAccent,
            onPressed: () => registerPeerConnectionListeners(),
            child: const Icon(Icons.settings_applications_rounded),
          ),
          const SizedBox(width: 10),
          FloatingActionButton(
            backgroundColor: Colors.green,
            onPressed: () => {makeCall()},
            child: const Icon(Icons.call_outlined),
          ),
          const SizedBox(width: 10),
          FloatingActionButton(
            backgroundColor: Colors.redAccent,
            onPressed: () {
              channel.sink.add(
                jsonEncode({"event": "msg", "data": "Hi this is an offer"}),
              );
            },
            child: const Icon(Icons.call_end_outlined),
          ),
        ],
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
    );
  }
}
