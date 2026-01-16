import { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera as CameraIcon, X, Check, RotateCcw } from 'lucide-react';
import toast from 'react-hot-toast';

const Camera = ({ onCapture, onClose, multiplePhotos = false, maxPhotos = 10 }) => {
    const webcamRef = useRef(null);
    const [capturedPhotos, setCapturedPhotos] = useState([]);
    const [isCameraReady, setIsCameraReady] = useState(false);

    const videoConstraints = {
        width: 1280,
        height: 720,
        facingMode: 'user',
    };

    const capture = useCallback(() => {
        const imageSrc = webcamRef.current.getScreenshot();

        if (!imageSrc) {
            toast.error('Failed to capture photo');
            return;
        }

        if (multiplePhotos) {
            if (capturedPhotos.length >= maxPhotos) {
                toast.error(`Maximum ${maxPhotos} photos allowed`);
                return;
            }

            setCapturedPhotos([...capturedPhotos, imageSrc]);
            toast.success(`Photo ${capturedPhotos.length + 1} captured`);
        } else {
            onCapture([imageSrc]);
            onClose();
        }
    }, [webcamRef, capturedPhotos, multiplePhotos, maxPhotos, onCapture, onClose]);

    const removePhoto = (index) => {
        setCapturedPhotos(capturedPhotos.filter((_, i) => i !== index));
    };

    const handleDone = () => {
        if (capturedPhotos.length < 3 && multiplePhotos) {
            toast.error('Please capture at least 3 photos');
            return;
        }

        onCapture(capturedPhotos);
        onClose();
    };

    const handleRetake = () => {
        setCapturedPhotos([]);
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-border">
                    <div>
                        <h2 className="text-xl font-bold text-text">
                            {multiplePhotos ? 'Capture Multiple Photos' : 'Capture Photo'}
                        </h2>
                        {multiplePhotos && (
                            <p className="text-sm text-gray-500 mt-1">
                                Capture {capturedPhotos.length}/{maxPhotos} photos (minimum 3)
                            </p>
                        )}
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Camera View */}
                <div className="p-4">
                    <div className="relative bg-black rounded-lg overflow-hidden">
                        <Webcam
                            ref={webcamRef}
                            audio={false}
                            screenshotFormat="image/jpeg"
                            videoConstraints={videoConstraints}
                            onUserMedia={() => setIsCameraReady(true)}
                            onUserMediaError={() => {
                                toast.error('Camera access denied');
                                onClose();
                            }}
                            className="w-full"
                            mirrored={true}
                        />

                        {!isCameraReady && (
                            <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                                <div className="text-center text-white">
                                    <CameraIcon className="w-12 h-12 mx-auto mb-2 animate-pulse" />
                                    <p>Initializing camera...</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Capture Button */}
                    {isCameraReady && (
                        <div className="mt-4 flex justify-center">
                            <button
                                onClick={capture}
                                className="btn btn-primary px-8 py-3 text-lg"
                                disabled={multiplePhotos && capturedPhotos.length >= maxPhotos}
                            >
                                <CameraIcon className="w-5 h-5 mr-2" />
                                Capture Photo
                            </button>
                        </div>
                    )}

                    {/* Captured Photos Preview */}
                    {capturedPhotos.length > 0 && (
                        <div className="mt-6">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-semibold text-text">
                                    Captured Photos ({capturedPhotos.length})
                                </h3>
                                <button
                                    onClick={handleRetake}
                                    className="btn btn-outline text-sm"
                                >
                                    <RotateCcw className="w-4 h-4 mr-1" />
                                    Retake All
                                </button>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                                {capturedPhotos.map((photo, index) => (
                                    <div key={index} className="relative group">
                                        <img
                                            src={photo}
                                            alt={`Captured ${index + 1}`}
                                            className="w-full h-32 object-cover rounded-lg border-2 border-border"
                                        />
                                        <button
                                            onClick={() => removePhoto(index)}
                                            className="absolute top-1 right-1 bg-error text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                        <div className="absolute bottom-1 left-1 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded">
                                            #{index + 1}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-4 flex justify-end space-x-3">
                                <button onClick={onClose} className="btn btn-outline">
                                    Cancel
                                </button>
                                <button
                                    onClick={handleDone}
                                    className="btn btn-secondary"
                                    disabled={capturedPhotos.length < 3}
                                >
                                    <Check className="w-4 h-4 mr-2" />
                                    Done ({capturedPhotos.length} photos)
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Camera;
