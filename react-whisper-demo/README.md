# React Whisper Real-time Transcription Demo

이 프로젝트는 FastRTC와 Groq의 Whisper 모델을 사용한 실시간 음성 인식 데모입니다.

## 설치 및 실행 방법

### 백엔드 서버 설정

1. 백엔드 서버(FastAPI)를 실행합니다:
   ```bash
   cd demo/whisper_realtime
   python app.py
   ```

### 프론트엔드(React) 설정

1. 의존성 설치:
   ```bash
   cd react-whisper-demo
   npm install
   ```

2. 개발 서버 실행:
   ```bash
   npm start
   ```

3. 브라우저에서 http://localhost:3000 으로 접속합니다.

## 개발 환경 설정

이 프로젝트는 다음과 같은 환경에서 개발되었습니다:
- Node.js 14.x 이상
- Python 3.8 이상

## 기능

- 실시간 음성 녹음 및 전송
- WebRTC를 통한 오디오 스트리밍
- Groq의 Whisper 모델을 이용한 음성 인식
- 실시간 트랜스크립트 표시

## 프록시 설정

React 앱은 백엔드 서버(http://localhost:7860)로 요청을 프록시합니다. 이 설정은 `package.json`의 "proxy" 필드에서 확인할 수 있습니다.

## 참고사항

- 마이크 접근 권한이 필요합니다.
- 브라우저는 WebRTC와 getUserMedia API를 지원해야 합니다.
- 백엔드 서버는 실행되고 있어야 React 앱이 제대로 작동합니다. 