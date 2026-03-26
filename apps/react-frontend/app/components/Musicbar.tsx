import { PlayIcon, PauseIcon, PrevIcon, NextIcon, VolumeIcon, LoopIcon, ShuffleIcon } from "./utilities/Icons";



function ArtistInfo({ songTitle, artistName, albumArtUrl }: { songTitle: string; artistName: string; albumArtUrl: string }) {
    return (
        <>
            <img
            src={albumArtUrl}
            alt="Album Art"
            className="w-12 h-12 object-cover rounded"
            />
            <div>
            <div className="font-semibold">{songTitle}</div>
            <div className="text-gray-400 text-sm">{artistName}</div>
            </div>
        </>
    );
}


function SongControls() {
    return (
        <div className="flex items-center gap-4">
            <button className="btn btn-ghost btn-circle hover:bg-gray-800">
            <ShuffleIcon />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800">
            <PrevIcon />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800">
            <PlayIcon />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800">
            <NextIcon />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800">
            <LoopIcon />
            </button>
        </div>
    );
}

function SongProgressBar({ currentTime, duration }: { currentTime: number; duration: number }) {
    const progress = (currentTime / duration) * 100;
    return (
        <div className="flex items-center gap-2 text-xs text-gray-400 w-64">
            <span>0:00</span>
            <input
            type="range"
            min={0}
            max={100}
            defaultValue={30}
            className="range range-xs range-primary flex-1"
            />
            <span>3:45</span>
        </div>
    );
}


export default function Musicbar() {

    // Artist info
    const songTitle = "Song Title";
    const songDuration = 225;
    const artistName = "Artist Name";
    const albumArtUrl = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQWNhdWPsAYJHHDhghY7c25HzzZdP1FTeahew&s";


    const currentTime = 90;

    return (
        <div className="bg-gray-900 text-white px-4 py-2 flex items-center justify-between shadow-inner fixed bottom-0 w-full">


            <div className="flex items-center gap-3">
                <ArtistInfo songTitle={songTitle} artistName={artistName} albumArtUrl={albumArtUrl} />
            </div>


            <div className="flex flex-col items-center gap-2">
                <SongControls />
                <SongProgressBar currentTime={currentTime} duration={songDuration} />
            </div>


            <div className="flex items-center gap-3">
                <button className="btn btn-ghost btn-circle hover:bg-gray-800">
                <VolumeIcon />
                </button>
            </div>


        </div>
    );
}
