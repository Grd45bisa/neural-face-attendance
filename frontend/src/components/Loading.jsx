import { Loader2 } from 'lucide-react';

const Loading = ({ text = 'Loading...' }) => {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen">
            <Loader2 className="w-12 h-12 text-primary animate-spin" />
            <p className="mt-4 text-text">{text}</p>
        </div>
    );
};

export default Loading;
