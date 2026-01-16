import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Camera as CameraIcon, CheckCircle, AlertCircle } from 'lucide-react';
import Camera from '../components/Camera';
import { faceAPI } from '../services/api';
import { dataURLtoBlob, blobToFile } from '../utils/helpers';
import toast from 'react-hot-toast';

const RegisterFace = () => {
    const [showCamera, setShowCamera] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleCapture = async (photos) => {
        setLoading(true);

        try {
            // Convert data URLs to File objects
            const photoFiles = photos.map((dataURL, index) => {
                const blob = dataURLtoBlob(dataURL);
                return blobToFile(blob, `photo_${index + 1}.jpg`);
            });

            // Upload to backend
            const response = await faceAPI.registerFace(photoFiles);

            toast.success(response.data.message);
            navigate('/dashboard');
        } catch (error) {
            console.error('Face registration error:', error);
            // Error toast already shown by interceptor
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="flex justify-center mb-4">
                        <div className="bg-secondary p-4 rounded-full">
                            <CameraIcon className="w-10 h-10 text-white" />
                        </div>
                    </div>
                    <h1 className="text-3xl font-bold text-text">Register Your Face</h1>
                    <p className="mt-2 text-gray-600">
                        Complete your registration by capturing your face photos
                    </p>
                </div>

                {/* Instructions Card */}
                <div className="card mb-6">
                    <h2 className="text-xl font-semibold text-text mb-4">Instructions</h2>

                    <div className="space-y-4">
                        <div className="flex items-start space-x-3">
                            <CheckCircle className="w-5 h-5 text-success mt-0.5" />
                            <div>
                                <p className="font-medium text-text">Capture 5-7 photos</p>
                                <p className="text-sm text-gray-600">
                                    Take photos from different angles (front, slight left, slight right)
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start space-x-3">
                            <CheckCircle className="w-5 h-5 text-success mt-0.5" />
                            <div>
                                <p className="font-medium text-text">Good lighting</p>
                                <p className="text-sm text-gray-600">
                                    Ensure your face is well-lit and clearly visible
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start space-x-3">
                            <CheckCircle className="w-5 h-5 text-success mt-0.5" />
                            <div>
                                <p className="font-medium text-text">Single face only</p>
                                <p className="text-sm text-gray-600">
                                    Make sure only your face is in the frame
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start space-x-3">
                            <AlertCircle className="w-5 h-5 text-warning mt-0.5" />
                            <div>
                                <p className="font-medium text-text">No accessories</p>
                                <p className="text-sm text-gray-600">
                                    Remove sunglasses, masks, or anything covering your face
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Action Button */}
                <div className="text-center">
                    <button
                        onClick={() => setShowCamera(true)}
                        className="btn btn-secondary px-8 py-3 text-lg"
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                                Registering...
                            </>
                        ) : (
                            <>
                                <CameraIcon className="w-5 h-5 mr-2" />
                                Start Camera
                            </>
                        )}
                    </button>

                    <p className="mt-4 text-sm text-gray-500">
                        You can skip this step and register later from your dashboard
                    </p>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="mt-2 text-primary hover:underline text-sm"
                    >
                        Skip for now
                    </button>
                </div>
            </div>

            {/* Camera Modal */}
            {showCamera && (
                <Camera
                    onCapture={handleCapture}
                    onClose={() => setShowCamera(false)}
                    multiplePhotos={true}
                    maxPhotos={10}
                />
            )}
        </div>
    );
};

export default RegisterFace;
