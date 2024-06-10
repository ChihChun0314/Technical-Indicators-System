

using Microsoft.AspNetCore.Mvc; // 引入 ASP.NET Core MVC 命名空間
using System.Diagnostics; // 引入診斷命名空間，用於執行外部進程
using Technical_Indicators_System.Models; // 引入模型命名空間

namespace Technical_Indicators_System.Controllers // 命名空間定義
{
    public class HomeController : Controller // 控制器類，繼承自 Controller
    {
        private readonly ILogger<HomeController> _logger; // 定義只讀的日誌記錄器

        public HomeController(ILogger<HomeController> logger) // 控制器構造函數，接受日誌記錄器參數
        {
            _logger = logger; // 初始化日誌記錄器
        }

        public IActionResult Index() // 處理 Index 請求
        {
            return View(); // 返回 Index 視圖
        }

        public IActionResult Privacy() // 處理 Privacy 請求
        {
            return View(); // 返回 Privacy 視圖
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)] // 禁用響應緩存
        public IActionResult Error() // 處理 Error 請求
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier }); // 返回 Error 視圖，並傳遞 ErrorViewModel
        }

        public IActionResult MACD() // 處理 MACD 請求
        {
            return View(); // 返回 MACD 視圖
        }

        [HttpPost] // 指定此方法處理 POST 請求
        public IActionResult ProcessMACDInputs(int ma1, int ma2, string stdate, string eddate, string ticker, int slicer)
        {
            // 調用 ExecutePythonScript 方法執行 Python 腳本，並將結果重定向到 MACDResult 方法
            return ExecutePythonScript("MACD_Oscillator_backtest.py", new object[] { ma1, ma2, stdate, eddate, ticker, slicer }, "MACDResult");
        }

        public IActionResult MACDResult() // 處理 MACDResult 請求
        {
            // 調用 GenerateResultView 方法生成結果視圖
            return GenerateResultView("MACDResult", "output_positions_MACD.png", "output_macd.png");
        }

        public IActionResult Pair() // 處理 Pair 請求
        {
            _logger.LogInformation("Pair action called."); // 記錄日誌信息
            return View(); // 返回 Pair 視圖
        }

        [HttpPost] // 指定此方法處理 POST 請求
        public IActionResult ProcessPairInputs(string stdate, string eddate, string ticker1, string ticker2)
        {
            // 記錄輸入參數的信息
            _logger.LogInformation($"ProcessPairInputs called with stdate: {stdate}, eddate: {eddate}, ticker1: {ticker1}, ticker2: {ticker2}");
            // 調用 ExecutePythonScript 方法執行 Python 腳本，並將結果重定向到 PairResult 方法
            return ExecutePythonScript("Pair_trading_backtest.py", new object[] { stdate, eddate, ticker1, ticker2 }, "PairResult");
        }

        public IActionResult PairResult() // 處理 PairResult 請求
        {
            _logger.LogInformation("PairResult action called."); // 記錄日誌信息
            // 調用 GenerateResultView 方法生成結果視圖
            return GenerateResultView("PairResult", "output_positions_Pair.png", "output_Pair_portfolio.png");
        }

        public IActionResult Heikin_Ashi() // 處理 Heikin_Ashi 請求
        {
            _logger.LogInformation("Heikin_Ashi action called."); // 記錄日誌信息
            return View(); // 返回 Heikin_Ashi 視圖
        }

        [HttpPost] // 指定此方法處理 POST 請求
        public IActionResult ProcessHeikin_AshiInputs(string ticker, string stdate, string eddate)
        {
            // 記錄輸入參數的信息
            _logger.LogInformation($"ProcessHeikin_AshiInputs called with stdate: {stdate}, eddate: {eddate}, ticker: {ticker}");
            // 調用 ExecutePythonScript 方法執行 Python 腳本，並將結果重定向到 Heikin_AshiResult 方法
            return ExecutePythonScript("Heikin_Ashi_backtest.py", new object[] { ticker, stdate, eddate }, "Heikin_AshiResult");
        }

        public IActionResult Heikin_AshiResult() // 處理 Heikin_AshiResult 請求
        {
            _logger.LogInformation("Heikin_AshiResult action called."); // 記錄日誌信息
            // 調用 GenerateResultView 方法生成結果視圖
            return GenerateResultView("Heikin_AshiResult", "output_positions_HeikinAshi.png", "output_HeikinAshi_portfolio.png");
        }

        private IActionResult ExecutePythonScript(string scriptName, object[] args, string resultAction)
        {
            try
            {
                // 設置 Python 腳本和執行檔路徑
                string pythonScriptPath = Path.Combine(Directory.GetCurrentDirectory(), "PythonScripts", "quant-trading-master", scriptName);
                string pythonExePath = @"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python39_64\python.exe"; // 修改為您的python.exe路徑
                string outputDir = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "images");

                // 設置 ProcessStartInfo 以執行 Python 腳本
                var start = new ProcessStartInfo
                {
                    FileName = pythonExePath,
                    Arguments = $"{pythonScriptPath} {string.Join(" ", args)} {outputDir}",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                };

                string result, error;
                using (var process = Process.Start(start)) // 開始進程
                {
                    using (var reader = process.StandardOutput) // 讀取標準輸出
                    {
                        result = reader.ReadToEnd();
                    }
                    using (var reader = process.StandardError) // 讀取標準錯誤
                    {
                        error = reader.ReadToEnd();
                    }
                }

                TempData["PythonOutput"] = result; // 將 Python 輸出存儲到 TempData
                TempData["PythonError"] = error; // 將 Python 錯誤信息存儲到 TempData
                for (int i = 0; i < args.Length; i++)
                {
                    TempData[$"Arg{i}"] = args[i].ToString(); // 將輸入參數存儲到 TempData
                }

                return RedirectToAction(resultAction); // 重定向到結果動作
            }
            catch (Exception ex)
            {
                TempData["PythonError"] = ex.Message; // 將異常信息存儲到 TempData
                return RedirectToAction(resultAction); // 重定向到結果動作
            }
        }

        private IActionResult GenerateResultView(string viewName, string positionsFileName, string macdFileName)
        {
            ViewBag.PythonOutput = TempData["PythonOutput"]; // 從 TempData 中獲取 Python 輸出並存儲到 ViewBag
            ViewBag.PythonError = TempData["PythonError"]; // 從 TempData 中獲取 Python 錯誤信息並存儲到 ViewBag

            for (int i = 0; TempData.ContainsKey($"Arg{i}"); i++) // 從 TempData 中獲取輸入參數並存儲到 ViewData
            {
                ViewData[$"Arg{i}"] = TempData[$"Arg{i}"];
            }

            // 設置圖片的路徑
            ViewBag.PositionsPath = Path.Combine("/images", positionsFileName);
            ViewBag.MacdPath = Path.Combine("/images", macdFileName);

            return View(viewName); // 返回指定的視圖名稱
        }
    }
}
