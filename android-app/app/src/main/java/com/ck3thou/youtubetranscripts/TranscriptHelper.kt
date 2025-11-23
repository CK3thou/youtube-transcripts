package com.ck3thou.youtubetranscripts

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class TranscriptHelper {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    suspend fun getTranscript(videoId: String): String = withContext(Dispatchers.IO) {
        try {
            // Fetch video page to get captions data
            val videoUrl = "https://www.youtube.com/watch?v=$videoId"
            val request = Request.Builder()
                .url(videoUrl)
                .addHeader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                .build()

            val response = client.newCall(request).execute()
            val html = response.body?.string() ?: throw Exception("Failed to fetch video page")

            // Extract captions URL from HTML
            val captionTracksPattern = Regex(""""captionTracks":\[(.*?)\]""")
            val match = captionTracksPattern.find(html)
                ?: throw Exception("No captions available for this video")

            val captionsJson = "[${match.groupValues[1]}]"
            val captionsArray = JSONArray(captionsJson)

            if (captionsArray.length() == 0) {
                throw Exception("No captions found")
            }

            // Get the first caption track (usually auto-generated or English)
            val firstCaption = captionsArray.getJSONObject(0)
            val baseUrl = firstCaption.getString("baseUrl")

            // Fetch the transcript
            val transcriptRequest = Request.Builder()
                .url(baseUrl)
                .build()

            val transcriptResponse = client.newCall(transcriptRequest).execute()
            val transcriptXml = transcriptResponse.body?.string()
                ?: throw Exception("Failed to fetch transcript")

            // Parse XML and extract text
            parseTranscriptXml(transcriptXml)

        } catch (e: Exception) {
            throw Exception("Failed to get transcript: ${e.message}")
        }
    }

    private fun parseTranscriptXml(xml: String): String {
        val textPattern = Regex("""<text[^>]*>([^<]*)</text>""")
        val matches = textPattern.findAll(xml)
        
        val transcript = matches.map { match ->
            val text = match.groupValues[1]
            // Decode HTML entities
            text.replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", "\"")
                .replace("&#39;", "'")
                .replace("\n", " ")
        }.joinToString(" ")

        if (transcript.isEmpty()) {
            throw Exception("No transcript text found")
        }

        return transcript
    }
}
