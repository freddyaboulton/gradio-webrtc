import React, { useState, useRef, useEffect } from 'react';
import './WhisperTranscription.css';

// 서버 API 기본 URL - 환경 변수가 설정되어 있으면 사용하고, 아니면 기본값 사용
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:7860';

const WhisperTranscription = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [transcripts, setTranscripts] = useState([]);
  const [errorMessage, setErrorMessage] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);

  // 개발 환경인지 확인
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  // API URL 생성 함수
  const getApiUrl = (path) => {
    // 개발 환경에서는 상대 경로 사용 (proxy 설정 활용)
    if (isDevelopment) {
      return path;
    }
    // 프로덕션 환경에서는 전체 URL 사용
    return `${API_BASE_URL}${path}`;
  };

  const peerConnectionRef = useRef(null);
  const webrtcIdRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const audioSourceRef = useRef(null);
  const animationFrameRef = useRef(null);
  const eventSourceRef = useRef(null);
  const transcriptContainerRef = useRef(null);

  const showError = (message) => {
    setErrorMessage(message);
    setTimeout(() => {
      setErrorMessage('');
    }, 5000);
  };

  const setupAudioVisualization = (stream) => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    const audioSource = audioContext.createMediaStreamSource(stream);
    
    audioSource.connect(analyser);
    analyser.fftSize = 64;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    audioContextRef.current = audioContext;
    analyserRef.current = analyser;
    audioSourceRef.current = audioSource;

    const updateAudioLevel = () => {
      analyser.getByteFrequencyData(dataArray);
      const average = Array.from(dataArray).reduce((a, b) => a + b, 0) / dataArray.length;
      const level = average / 255;
      setAudioLevel(level);
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    };
    
    updateAudioLevel();
  };

  const handleMessage = (event) => {
    const eventJson = JSON.parse(event.data);
    if (eventJson.type === "error") {
      showError(eventJson.message);
    }
    console.log('Received message:', event.data);
  };

  const setupWebRTC = async () => {
    setIsConnecting(true);
    const timeoutId = setTimeout(() => {
      showError("Connection is taking longer than usual. Are you on a VPN?");
    }, 5000);

    try {
      // Get RTC configuration from server if needed
      let rtcConfiguration = null;
      
      // Create peer connection
      peerConnectionRef.current = new RTCPeerConnection(rtcConfiguration);
      
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true
      });
      
      // Setup audio visualization
      setupAudioVisualization(stream);
      
      // Add tracks to peer connection
      stream.getTracks().forEach(track => {
        peerConnectionRef.current.addTrack(track, stream);
      });
      
      // Handle connection state changes
      peerConnectionRef.current.addEventListener('connectionstatechange', () => {
        console.log('Connection state:', peerConnectionRef.current.connectionState);
        if (peerConnectionRef.current.connectionState === 'connected') {
          clearTimeout(timeoutId);
          setIsConnecting(false);
          setIsRecording(true);
        }
      });
      
      // Create data channel
      const dataChannel = peerConnectionRef.current.createDataChannel('text');
      dataChannel.onmessage = handleMessage;
      
      // Create and set local description
      const offer = await peerConnectionRef.current.createOffer();
      await peerConnectionRef.current.setLocalDescription(offer);
      
      // Wait for ICE gathering to complete
      await new Promise((resolve) => {
        if (peerConnectionRef.current.iceGatheringState === "complete") {
          resolve();
        } else {
          const checkState = () => {
            if (peerConnectionRef.current.iceGatheringState === "complete") {
              peerConnectionRef.current.removeEventListener("icegatheringstatechange", checkState);
              resolve();
            }
          };
          peerConnectionRef.current.addEventListener("icegatheringstatechange", checkState);
        }
      });
      
      // Generate unique ID for this connection
      webrtcIdRef.current = Math.random().toString(36).substring(7);
      
      // Send offer to server
      const response = await fetch(getApiUrl('/webrtc/offer'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sdp: peerConnectionRef.current.localDescription.sdp,
          type: peerConnectionRef.current.localDescription.type,
          webrtc_id: webrtcIdRef.current
        })
      });
      
      const serverResponse = await response.json();
      
      if (serverResponse.status === 'failed') {
        showError(serverResponse.meta.error === 'concurrency_limit_reached'
          ? `Too many connections. Maximum limit is ${serverResponse.meta.limit}`
          : serverResponse.meta.error);
        stopRecording();
        return;
      }
      
      // Set remote description from server response
      await peerConnectionRef.current.setRemoteDescription(serverResponse);
      
      // Create event source for receiving transcripts
      eventSourceRef.current = new EventSource(getApiUrl(`/transcript?webrtc_id=${webrtcIdRef.current}`));
      eventSourceRef.current.addEventListener("output", (event) => {
        setTranscripts(prev => [...prev, event.data]);
        // Scroll to bottom of transcript container
        if (transcriptContainerRef.current) {
          transcriptContainerRef.current.scrollTop = transcriptContainerRef.current.scrollHeight;
        }
      });
      
    } catch (err) {
      clearTimeout(timeoutId);
      console.error('Error setting up WebRTC:', err);
      showError('Failed to establish connection. Please try again.');
      stopRecording();
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    setIsConnecting(false);
    
    // Cancel animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
      analyserRef.current = null;
      audioSourceRef.current = null;
    }
    
    // Close peer connection
    if (peerConnectionRef.current) {
      // Stop all transceivers
      if (peerConnectionRef.current.getTransceivers) {
        peerConnectionRef.current.getTransceivers().forEach(transceiver => {
          if (transceiver.stop) {
            transceiver.stop();
          }
        });
      }
      
      // Stop all tracks
      if (peerConnectionRef.current.getSenders) {
        peerConnectionRef.current.getSenders().forEach(sender => {
          if (sender.track && sender.track.stop) sender.track.stop();
        });
      }
      
      // Close connection after a short delay
      setTimeout(() => {
        peerConnectionRef.current.close();
        peerConnectionRef.current = null;
      }, 500);
    }
    
    // Close event source
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    setAudioLevel(0);
  };

  const toggleRecording = () => {
    if (isRecording || isConnecting) {
      stopRecording();
    } else {
      setupWebRTC();
    }
  };

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  return (
    <div className="whisper-transcription">
      {errorMessage && (
        <div className="error-toast">{errorMessage}</div>
      )}
      
      <div className="transcript-container" ref={transcriptContainerRef}>
        {transcripts.map((text, index) => (
          <p key={index}>{text}</p>
        ))}
      </div>
      
      <div className="controls">
        <button 
          className="control-button" 
          onClick={toggleRecording}
        >
          {isConnecting ? (
            <div className="button-content">
              <div className="spinner"></div>
              <span>연결 중...</span>
            </div>
          ) : isRecording ? (
            <div className="button-content">
              <div 
                className="pulse-circle" 
                style={{ transform: `translateX(-0%) scale(${1 + audioLevel})` }}
              ></div>
              <span>녹음 중지</span>
            </div>
          ) : (
            <span>녹음 시작</span>
          )}
        </button>
      </div>
      
      <div className="server-info">
        <p>서버 연결: {API_BASE_URL}</p>
      </div>
    </div>
  );
};

export default WhisperTranscription; 