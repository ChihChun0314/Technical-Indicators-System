using Microsoft.Extensions.Options;
using Technical_Indicators_System;

var builder = WebApplication.CreateBuilder(args);

// 添加配置服務
builder.Services.Configure<GlobalSettings>(builder.Configuration.GetSection("GlobalSettings"));
builder.Services.AddSingleton(resolver => resolver.GetRequiredService<IOptions<GlobalSettings>>().Value);
// Add services to the container.
builder.Services.AddControllersWithViews();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();

app.UseAuthorization();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

app.Run();