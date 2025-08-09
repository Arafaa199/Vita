(function(){
  const root = document.documentElement;
  const key = "vita-theme";
  function setTheme(mode){
    if(mode==="light"){ root.classList.add("light"); localStorage.setItem(key,"light"); }
    else{ root.classList.remove("light"); localStorage.setItem(key,"dark"); }
  }
  const saved = localStorage.getItem(key) || "dark";
  setTheme(saved);
  document.addEventListener("click",(e)=>{
    const b=e.target.closest("[data-theme-toggle]");
    if(!b) return;
    setTheme(root.classList.contains("light") ? "dark":"light");
  });
})();
