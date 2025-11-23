package com.ck3thou.youtubetranscripts

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.ck3thou.youtubetranscripts.databinding.ActivityMainBinding
import kotlinx.coroutines.*
import java.io.File
import java.io.FileOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var videoList: List<VideoInfo> = listOf()
    private var isPlaylist = false
    private val STORAGE_PERMISSION_CODE = 100

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupListeners()
        checkStoragePermission()
    }

    private fun setupListeners() {
        binding.loadButton.setOnClickListener {
            val url = binding.urlInput.text.toString().trim()
            if (url.isEmpty()) {
                Toast.makeText(this, "Please enter a URL", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            loadUrl(url)
        }

        binding.downloadButton.setOnClickListener {
            startDownload()
        }

        binding.startVideoSpinner.onItemSelectedListener = object : android.widget.AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: android.widget.AdapterView<*>?, view: View?, position: Int, id: Long) {
                updateVideoList(position)
            }

            override fun onNothingSelected(parent: android.widget.AdapterView<*>?) {}
        }
    }

    private fun checkStoragePermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(
                    this,
                    arrayOf(Manifest.permission.WRITE_EXTERNAL_STORAGE),
                    STORAGE_PERMISSION_CODE
                )
            }
        }
    }

    private fun loadUrl(url: String) {
        binding.loadButton.isEnabled = false
        binding.progressBar.visibility = View.VISIBLE
        log("Loading URL...")

        scope.launch {
            try {
                val helper = YouTubeHelper()
                isPlaylist = helper.isPlaylist(url)

                if (isPlaylist) {
                    videoList = withContext(Dispatchers.IO) {
                        helper.getPlaylistVideos(url)
                    }
                    log("Found ${videoList.size} videos in playlist")
                    setupPlaylistUI()
                } else {
                    val videoInfo = withContext(Dispatchers.IO) {
                        helper.getSingleVideo(url)
                    }
                    videoList = mutableListOf(videoInfo)
                    log("Loaded video: ${videoInfo.title}")
                    setupSingleVideoUI()
                }

                binding.videoListSection.visibility = View.VISIBLE
                binding.downloadButton.visibility = View.VISIBLE

            } catch (e: Exception) {
                log("Error: ${e.message}")
                Toast.makeText(this@MainActivity, "Error: ${e.message}", Toast.LENGTH_LONG).show()
            } finally {
                binding.loadButton.isEnabled = true
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun setupPlaylistUI() {
        binding.playlistSection.visibility = View.VISIBLE
        val items = videoList.mapIndexed { index, video ->
            "${index + 1}. ${video.title}"
        }
        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, items)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        binding.startVideoSpinner.adapter = adapter
        updateVideoList(0)
    }

    private fun setupSingleVideoUI() {
        binding.playlistSection.visibility = View.GONE
        updateVideoList(0)
    }

    private fun updateVideoList(startIndex: Int) {
        val videosToShow = videoList.subList(startIndex, videoList.size)
        binding.videoCount.text = videosToShow.size.toString()
        
        val listText = videosToShow.mapIndexed { index, video ->
            "${startIndex + index + 1}. ${video.title}"
        }.joinToString("\n\n")
        
        binding.videoListText.text = listText
    }

    private fun startDownload() {
        val startIndex = if (isPlaylist) binding.startVideoSpinner.selectedItemPosition else 0
        
        binding.downloadButton.isEnabled = false
        binding.progressBar.visibility = View.VISIBLE
        binding.progressText.visibility = View.VISIBLE
        
        log("Starting download...")

        scope.launch {
            val transcriptHelper = TranscriptHelper()
            val results = mutableListOf<TranscriptResult>()
            val total = videoList.size - startIndex

            for (i in startIndex until videoList.size) {
                if (!binding.downloadButton.isEnabled && i > startIndex) break // Cancelled

                val video = videoList[i]
                val progress = ((i - startIndex + 1) * 100) / total
                
                withContext(Dispatchers.Main) {
                    binding.progressBar.progress = progress
                    binding.progressText.text = "Processing ${i + 1}/${videoList.size}"
                    log("\n[${i + 1}/${videoList.size}] Processing: ${video.title}")
                }

                try {
                    delay(5000) // Rate limiting
                    val transcript = withContext(Dispatchers.IO) {
                        transcriptHelper.getTranscript(video.id)
                    }
                    
                    results.add(TranscriptResult(video, transcript, true, null))
                    log("✓ ${video.title}")
                } catch (e: Exception) {
                    results.add(TranscriptResult(video, "", false, e.message))
                    log("✗ ${video.title}: ${e.message}")
                }
            }

            // Save results
            val successCount = results.count { it.success }
            val errorCount = results.count { !it.success }
            
            if (successCount > 0) {
                saveTranscripts(results.filter { it.success })
            }

            log("\nCompleted! $successCount successful, $errorCount failed")
            Toast.makeText(
                this@MainActivity,
                "Downloaded $successCount transcripts",
                Toast.LENGTH_LONG
            ).show()

            binding.downloadButton.isEnabled = true
            binding.progressBar.visibility = View.GONE
            binding.progressText.visibility = View.GONE
        }
    }

    private fun saveTranscripts(results: List<TranscriptResult>) {
        try {
            val folder = File(
                Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
                "YouTubeTranscripts"
            )
            folder.mkdirs()

            results.forEachIndexed { index, result ->
                val video = result.video
                val safeTitle = video.title.replace(Regex("[<>:\"/\\\\|?*]"), "")
                val filename = String.format("%02d_%s.txt", index + 1, safeTitle)
                val file = File(folder, filename)

                file.writeText("""
                    Video ID: ${video.id}
                    Title: ${video.title}
                    URL: ${video.url}
                    ${"-".repeat(80)}
                    
                    ${result.transcript}
                """.trimIndent())
            }

            log("\nTranscripts saved to: ${folder.absolutePath}")
            Toast.makeText(
                this,
                "Saved to Downloads/YouTubeTranscripts",
                Toast.LENGTH_LONG
            ).show()

        } catch (e: Exception) {
            log("Error saving files: ${e.message}")
            Toast.makeText(this, "Error saving: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private fun log(message: String) {
        val currentLog = binding.logText.text.toString()
        binding.logText.text = "$currentLog\n$message"
        binding.logScrollView.post {
            binding.logScrollView.fullScroll(View.FOCUS_DOWN)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        scope.cancel()
    }
}

data class VideoInfo(
    val id: String,
    val title: String,
    val url: String
)

data class TranscriptResult(
    val video: VideoInfo,
    val transcript: String,
    val success: Boolean,
    val error: String?
)
