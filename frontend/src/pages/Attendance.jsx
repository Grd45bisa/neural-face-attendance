import { useState } from 'react';
import { Camera as CameraIcon, CheckCircle2, AlertCircle } from 'lucide-react';
import Navbar from '../components/Navbar';
import Camera from '../components/Camera';
import { faceAPI } from '../services/api';
import { dataURLtoBlob, blobToFile } from '../utils/helpers';
import toast from 'react-hot-toast';

const Attendance = () => {
    const [showCamera, setShowCamera] = useState(false);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handleCapture = async (photos) => {
        setLoading(true);
        setResult(null);

        try {
            // Convert data URL to File
            const blob = dataURLtoBlob(photos[0]);
            const photoFile = blobToFile(blob, 'attendance.jpg');

            // Verify face
            const response = await faceAPI.verifyFace(photoFile);

            setResult({
                success: true,
                data: response.data.data,
            });

            toast.success('Attendance recorded successfully!');
        } catch (error) {
            setResult({
                success: false,
                message: error.response?.data?.message || 'Verification failed',
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-text">Mark Attendance</h1>
                    <p className="mt-2 text-gray-600">
                        Capture your photo to verify and mark attendance
                    </p>
                </div>

                {/* Main Card */}
                <div className="card">
                    {!result ? (
                        <div className="text-center py-8">
                            <div className="flex justify-center mb-6">
                                <div className="bg-primary p-6 rounded-full">
                                    <CameraIcon className="w-12 h-12 text-white" />
                                </div>
                            </div>

                            <h2 className="text-xl font-semibold text-text mb-2">
                                Ready to mark attendance?
                            </h2>
                            <p className="text-gray-600 mb-6">
                                Click the button below to capture your photo
                            </p>

                            <button
                                onClick={() => setShowCamera(true)}
                                className="btn btn-primary px-8 py-3 text-lg"
                                disabled={loading}
                            >
                                {loading ? (
                                    <>
                                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                                        Verifying...
                                    </>
                                ) : (
                                    <>
                                        <CameraIcon className="w-5 h-5 mr-2" />
                                        Capture Photo
                                    </>
                                )}
                            </button>

                            <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <h3 className="font-semibold text-text mb-2">Tips for best results:</h3>
                                <ul className="text-sm text-gray-600 space-y-1 text-left max-w-md mx-auto">
                                    <li>• Ensure good lighting on your face</li>
                                    <li>• Look directly at the camera</li>
                                    <li>• Remove sunglasses or masks</li>
                                    <li>• Keep your face centered in the frame</li>
                                </ul>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center py-8">
                            {result.success ? (
                                <>
                                    <div className="flex justify-center mb-6">
                                        <div className="bg-success p-6 rounded-full">
                                            <CheckCircle2 className="w-12 h-12 text-white" />
                                        </div>
                                    </div>

                                    <h2 className="text-2xl font-bold text-success mb-2">
                                        Attendance Recorded!
                                    </h2>
                                    <p className="text-gray-600 mb-6">
                                        Your attendance has been successfully marked
                                    </p>

                                    <div className="bg-gray-50 rounded-lg p-6 max-w-md mx-auto mb-6">
                                        <div className="space-y-3 text-left">
                                            <div className="flex justify-between">
                                                <span className="text-gray-600">Confidence:</span>
                                                <span className="font-semibold text-text">
                                                    {(result.data.confidence * 100).toFixed(1)}%
                                                </span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-gray-600">Time:</span>
                                                <span className="font-semibold text-text">
                                                    {new Date().toLocaleTimeString()}
                                                </span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-gray-600">Status:</span>
                                                <span className="badge badge-success">
                                                    {result.data.attendance.status}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <button
                                        onClick={() => setResult(null)}
                                        className="btn btn-outline"
                                    >
                                        Mark Another Attendance
                                    </button>
                                </>
                            ) : (
                                <>
                                    <div className="flex justify-center mb-6">
                                        <div className="bg-error p-6 rounded-full">
                                            <AlertCircle className="w-12 h-12 text-white" />
                                        </div>
                                    </div>

                                    <h2 className="text-2xl font-bold text-error mb-2">
                                        Verification Failed
                                    </h2>
                                    <p className="text-gray-600 mb-6">{result.message}</p>

                                    <button
                                        onClick={() => setResult(null)}
                                        className="btn btn-primary"
                                    >
                                        Try Again
                                    </button>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Camera Modal */}
            {showCamera && (
                <Camera
                    onCapture={handleCapture}
                    onClose={() => setShowCamera(false)}
                    multiplePhotos={false}
                />
            )}
        </div>
    );
};

export default Attendance;
