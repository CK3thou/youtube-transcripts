package com.ck3thou.youtubetranscripts

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.jsoup.Jsoup
import java.util.concurrent.TimeUnit

class YouTubeHelper {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    fun isPlaylist(url: String): Boolean {
        return url.contains("list=")
    }

    fun extractVideoId(url: String): String? {
        return when {
            url.contains("watch?v=") -> {
                url.substringAfter("watch?v=").substringBefore("&")
            }
            url.contains("youtu.be/") -> {
                url.substringAfter("youtu.be/").substringBefore("?")
            }
            else -> null
        }
    }

    suspend fun getSingleVideo(url: String): VideoInfo = withContext(Dispatchers.IO) {
        val videoId = extractVideoId(url) ?: throw Exception("Invalid YouTube URL")
        val title = getVideoTitle(url) ?: videoId
        VideoInfo(videoId, title, url)
    }

    suspend fun getPlaylistVideos(playlistUrl: String): List<VideoInfo> = withContext(Dispatchers.IO) {
        val videoList = mutableListOf<VideoInfo>()
        
        try {
            val request = Request.Builder()
                .url(playlistUrl)
                .addHeader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                .build()

            val response = client.newCall(request).execute()
            val html = response.body?.string() ?: throw Exception("Failed to fetch playlist")

            // Extract video IDs from HTML
            val videoIdPattern = Regex(""""videoId":"([a-zA-Z0-9_-]{11})"""")
            val matches = videoIdPattern.findAll(html)
            
            val seenIds = mutableSetOf<String>()
            matches.forEach { match ->
                val videoId = match.groupValues[1]
                if (videoId !in seenIds) {
                    seenIds.add(videoId)
                    val videoUrl = "https://www.youtube.com/watch?v=$videoId"
                    val title = getVideoTitle(videoUrl) ?: "Video ${seenIds.size}"
                    videoList.add(VideoInfo(videoId, title, videoUrl))
                }
            }

        } catch (e: Exception) {
            throw Exception("Failed to load playlist: ${e.message}")
        }

        if (videoList.isEmpty()) {
            throw Exception("No videos found in playlist")
        }

        videoList
    }

    private fun getVideoTitle(url: String): String? {
        return try {
            val request = Request.Builder()
                .url(url)
                .addHeader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                .build()

            val response = client.newCall(request).execute()
            val html = response.body?.string() ?: return null

            // Try multiple patterns to extract title
            val patterns = listOf(
                Regex(""""title":"([^"]+)""""),
                Regex("""<title>([^<]+)</title>"""),
                Regex("""property="og:title" content="([^"]+)"""")
            )

            for (pattern in patterns) {
                val match = pattern.find(html)
                if (match != null) {
                    var title = match.groupValues[1]
                    title = title.replace(" - YouTube", "").trim()
                    return title
                }
            }

            null
        } catch (e: Exception) {
            null
        }
    }
}
