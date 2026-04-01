
export interface PlaybackStatus {
    playing : boolean;
    paused : boolean;
    position : number;
    source_url : string;
    volume : number;
    video_id: string;
    ended: boolean;
    loop: boolean;
}
