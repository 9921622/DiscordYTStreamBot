

export function NumToTime(num: number): string {
    const minutes = Math.floor(num / 60);
    const seconds = Math.floor(num % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}
