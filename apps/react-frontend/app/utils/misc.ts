

export function stringify(obj : any) {
    // Convert a JavaScript object to a URL-encoded query string.
    return Object.keys(obj)
        .map(key => encodeURIComponent(key) + '=' + encodeURIComponent(obj[key]))
        .join('&');
}
