package com.astrabio.app

import android.graphics.Color
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.github.mikephil.charting.charts.BarChart
import com.github.mikephil.charting.data.BarData
import com.github.mikephil.charting.data.BarDataSet
import com.github.mikephil.charting.data.BarEntry
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader

class MainActivity : AppCompatActivity() {

    private lateinit var resultsView: TextView
    private lateinit var chart: BarChart
    private lateinit var spinner: ProgressBar
    private lateinit var osdrInput: EditText

    // Picked CSV contents (parsed to simple numeric tables)
    private var earthTable: Pair<List<String>, List<List<Double>>>? = null
    private var spaceTable: Pair<List<String>, List<List<Double>>>? = null
    private lateinit var statusEarth: TextView
    private lateinit var statusSpace: TextView

    private val pickEarth = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { earthTable = readCsv(it); statusEarth.text = "Earth: ${it.lastPathSegment}" }
    }
    private val pickSpace = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { spaceTable = readCsv(it); statusSpace.text = "Space: ${it.lastPathSegment}" }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        resultsView = findViewById(R.id.results)
        chart = findViewById(R.id.chart)
        spinner = findViewById(R.id.spinner)
        osdrInput = findViewById(R.id.osdr_accession)
        statusEarth = findViewById(R.id.status_earth)
        statusSpace = findViewById(R.id.status_space)

        findViewById<Button>(R.id.btn_demo).setOnClickListener { runDemo() }
        findViewById<Button>(R.id.btn_pick_earth).setOnClickListener { pickEarth.launch("text/*") }
        findViewById<Button>(R.id.btn_pick_space).setOnClickListener { pickSpace.launch("text/*") }
        findViewById<Button>(R.id.btn_analyze).setOnClickListener { runUploaded() }
        findViewById<Button>(R.id.btn_osdr).setOnClickListener { runOsdr() }
    }

    // ------------------------------------------------------------------ demo
    private fun runDemo() = inBackground {
        val py = Python.getInstance()
        val json = py.getModule("astra_engine").callAttr("demo_analysis").toString()
        val root = JSONObject(json)
        val pheno = root.getJSONArray("phenotypes")

        runOnUiThread { showPhenoChart(pheno) }

        val sb = StringBuilder()
        sb.append("PHENOTYPES\n").append(phenoTable(pheno)).append("\n\n")
        for (key in listOf("transcriptomics", "proteomics", "metabolomics")) {
            sb.append(key.uppercase()).append("\n")
                .append(hitsTable(root.getJSONArray(key), 10)).append("\n\n")
        }
        sb.append("Demo ran fully offline (Python + NumPy + SciPy inside the APK).")
        showText(sb.toString())
    }

    // --------------------------------------------------------------- uploads
    private fun runUploaded() = inBackground {
        val e = earthTable ?: return@inBackground showText("Pick an Earth CSV first.")
        val s = spaceTable ?: return@inBackground showText("Pick a Space CSV first.")
        val cols = e.first.intersect(s.first.toSet()).toList()
        if (cols.isEmpty()) return@inBackground showText("No shared numeric columns between the two files.")

        fun tableJson(t: Pair<List<String>, List<List<Double>>>, keep: List<String>): String {
            val idx = keep.map { t.first.indexOf(it) }
            val rows = JSONArray()
            for (r in t.second) rows.put(JSONArray(idx.map { r[it] }))
            return JSONObject().put("columns", JSONArray(keep)).put("rows", rows).toString()
        }

        val py = Python.getInstance()
        val json = py.getModule("astra_engine")
            .callAttr("analyze_uploaded", tableJson(e, cols), tableJson(s, cols), "null")
            .toString()
        val arr = JSONArray(json)

        runOnUiThread { showPhenoChart(arr) }
        showText("UPLOADED PHENOTYPES (${cols.joinToString(", ")})\n\n" + phenoTable(arr))
    }

    // ------------------------------------------------------------------ OSDR
    private fun runOsdr() = inBackground {
        val acc = osdrInput.text.toString().trim()
        if (acc.isEmpty()) return@inBackground showText("Enter an accession, e.g. OSD-48")
        try {
            val py = Python.getInstance()
            val jsonText = py.getModule("osdr_query")
                .callAttr("dataset_metadata", acc).toString()
            val pretty = JSONObject(jsonText).toString(2)
            showText("OSDR $acc metadata (first 6000 chars):\n\n" + pretty.take(6000))
        } catch (ex: Exception) {
            showText("OSDR query failed (need internet):\n${ex.message}")
        }
    }

    // ----------------------------------------------------------------- helpers
    private fun readCsv(uri: android.net.Uri): Pair<List<String>, List<List<Double>>>? {
        val rows = mutableListOf<List<Double>>()
        var header: List<String>? = null
        contentResolver.openInputStream(uri)?.use { ins ->
            BufferedReader(InputStreamReader(ins)).useLines { lines ->
                for (line in lines) {
                    val cells = line.split(",").map { it.trim() }
                    if (header == null) { header = cells; continue }
                    val nums = cells.map { it.toDoubleOrNull() }
                    if (nums.any { it == null }) continue  // skip non-numeric rows
                    rows.add(nums.map { it!! })
                }
            }
        }
        val h = header ?: return null
        if (rows.isEmpty()) return null
        return h to rows
    }

    private fun showPhenoChart(arr: JSONArray) {
        val earth = ArrayList<BarEntry>()
        val space = ArrayList<BarEntry>()
        val labels = ArrayList<String>()
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            earth.add(BarEntry(i.toFloat(), o.getDouble("earth_mean").toFloat()))
            space.add(BarEntry(i.toFloat(), o.getDouble("space_mean").toFloat()))
            labels.add(o.getString("feature"))
        }
        val dsE = BarDataSet(earth, "Earth").apply { color = Color.parseColor("#1f6feb") }
        val dsS = BarDataSet(space, "Spaceflight").apply { color = Color.parseColor("#f85149") }
        chart.apply {
            data = BarData(dsE, dsS)
            xAxis.valueFormatter = com.github.mikephil.charting.formatter.IndexAxisValueFormatter(labels)
            xAxis.granularity = 1f
            description.text = "Phenotype means"
            groupBars(0f, 0.2f, 0.05f)
            fitScreen(); invalidate()
        }
    }

    private fun phenoTable(arr: JSONArray): String = buildString {
        append(String.format("%-16s %8s %8s %7s %10s  %s\n", "feature", "earth", "space", "fold", "p_adj", "effect"))
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            append(String.format("%-16s %8.3f %8.3f %7.2f %10.2e  %s\n",
                o.getString("feature"), o.getDouble("earth_mean"), o.getDouble("space_mean"),
                o.optDouble("fold_change", Double.NaN), o.getDouble("p_value_adj"),
                o.getString("effect_size")))
        }
    }

    private fun hitsTable(arr: JSONArray, limit: Int): String = buildString {
        append(String.format("%-12s %8s %12s  %s\n", "feature", "log2FC", "p_adj", "sig"))
        var shown = 0
        for (i in 0 until arr.length()) {
            if (shown >= limit) break
            val o = arr.getJSONObject(i)
            append(String.format("%-12s %8.2f %12.2e  %s\n",
                o.getString("feature"), o.getDouble("log2_fold_change"),
                o.getDouble("p_value_adj"), if (o.getBoolean("significant")) "YES" else "-"))
            shown++
        }
    }

    private fun inBackground(block: () -> Unit) {
        spinner.visibility = View.VISIBLE
        Thread {
            try { block() }
            catch (ex: Exception) { runOnUiThread { showText("Error:\n${ex.message}") } }
            finally { runOnUiThread { spinner.visibility = View.GONE } }
        }.start()
    }

    private fun showText(text: String) = runOnUiThread {
        resultsView.text = text
        Toast.makeText(this, "Done", Toast.LENGTH_SHORT).show()
    }
}
