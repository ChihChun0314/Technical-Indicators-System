using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using Technical_Indicators_System.Models;

namespace Technical_Indicators_System.Controllers
{
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;

        public HomeController(ILogger<HomeController> logger)
        {
            _logger = logger;
        }

        public IActionResult Index()
        {
            return View();
        }

        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }

        public IActionResult MACD()
        {
            return View();
        }
        [HttpPost]
        public IActionResult ProcessMACDInputs(int ma1, int ma2, string stdate, string eddate, string ticker, int slicer)
        {
            // 將輸入值傳遞給 ViewBag
            ViewBag.Ma1 = ma1;
            ViewBag.Ma2 = ma2;
            ViewBag.Stdate = stdate;
            ViewBag.Eddate = eddate;
            ViewBag.Ticker = ticker;
            ViewBag.Slicer = slicer;

            // 設置 Python 腳本和執行檔路徑
            string pythonScriptPath = @"C:\Users\Jason\Desktop\Technical Indicators System\Technical Indicators System\PythonScripts\quant-trading-master\MACD Oscillator backtest.py";
            string pythonExePath = @"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python39_64\python.exe";

            // 設置 ProcessStartInfo 以執行 Python 腳本
            ProcessStartInfo start = new ProcessStartInfo();
            start.FileName = pythonExePath;
            start.Arguments = $"{pythonScriptPath} {ma1} {ma2} {stdate} {eddate} {ticker} {slicer}"; // 將輸入參數傳遞給 Python 腳本
            start.UseShellExecute = false;
            start.RedirectStandardOutput = true;
            start.RedirectStandardError = true;

            string result = "";
            using (Process process = Process.Start(start))
            {
                using (StreamReader reader = process.StandardOutput)
                {
                    result = reader.ReadToEnd();
                }
            }

            // 將 Python 腳本的輸出存儲到 TempData 以便在重定向後使用
            TempData["PythonOutput"] = result;
            TempData["Ma1"] = ma1;
            TempData["Ma2"] = ma2;
            TempData["Stdate"] = stdate;
            TempData["Eddate"] = eddate;
            TempData["Ticker"] = ticker;
            TempData["Slicer"] = slicer;

            // 返回 MACD 視圖，使用 TempData 傳遞數據
            return RedirectToAction("MACDResult");
        }
        public IActionResult MACDResult()
        {
            // 將 TempData 中的數據存儲到 ViewBag
            ViewBag.PythonOutput = TempData["PythonOutput"];
            ViewBag.Ma1 = TempData["Ma1"];
            ViewBag.Ma2 = TempData["Ma2"];
            ViewBag.Stdate = TempData["Stdate"];
            ViewBag.Eddate = TempData["Eddate"];
            ViewBag.Ticker = TempData["Ticker"];
            ViewBag.Slicer = TempData["Slicer"];

            // 獲取圖片路徑
            string positionsPath = Path.Combine("~/images", "output_positions.png");
            string macdPath = Path.Combine("~/images", "output_macd.png");
            ViewBag.PositionsPath = positionsPath;
            ViewBag.MacdPath = macdPath;

            return View();
        }
    }
}
