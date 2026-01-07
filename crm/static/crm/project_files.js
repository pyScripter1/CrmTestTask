document.addEventListener("DOMContentLoaded", () => {

  /* ================= CSRF ================= */

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  const CSRF_TOKEN = getCookie("csrftoken");

  /* ================= ELEMENTS ================= */

  const dropzone = document.getElementById("dropzone");
  const input = document.getElementById("file-input");
  const tree = document.getElementById("file-tree");
  const createRootFolderBtn = document.getElementById("create-root-folder");
  const selectRoot = document.getElementById("select-root");

  let currentFolder = null; // null = корень
  let openFolders = new Set();


  /* ================= LOAD TREE ================= */

  async function loadTree() {
    const r = await fetch(`/api/projects/${PROJECT_UUID}/files/tree/`, {
      credentials: "same-origin"
    });

    if (!r.ok) {
      tree.innerHTML = "<p>Нет доступа к файлам проекта</p>";
      return;
    }

    const data = await r.json();
    tree.innerHTML = "";

    const root = data.root || {};
    const rootFiles = root.files || [];
    const rootFolders = root.folders || [];

    renderFiles(rootFiles, tree);
    rootFolders.forEach(folder => renderFolder(folder, tree));
  }

  /* ================= FILES ================= */

  function renderFiles(files, container) {
    if (!files || !files.length) return;

    files
      .slice()
      .sort((a, b) => a.filename.localeCompare(b.filename))
      .forEach(f => {
        const row = document.createElement("div");
        row.className = "file-row";
        row.draggable = true;

        row.ondragstart = e => {
          e.dataTransfer.setData("file_uuid", f.uuid);
        };

        const link = document.createElement("a");
        link.className = "file";
        link.href = f.url;
        link.textContent = "📄 " + f.filename;
        link.target = "_blank";

        const del = document.createElement("button");
        del.className = "file-delete";
        del.textContent = "🗑️";

        del.onclick = async () => {
          if (!confirm(`Удалить файл "${f.filename}"?`)) return;

          const r = await fetch(
            `/api/projects/${PROJECT_UUID}/files/${f.uuid}/delete/`,
            {
              method: "DELETE",
              credentials: "same-origin",
              headers: { "X-CSRFToken": CSRF_TOKEN }
            }
          );

          if (r.ok) loadTree();
          else alert("Нет прав на удаление файла");
        };

        const name = document.createElement("span");
        name.className = "file-name";
        name.appendChild(link);

        row.appendChild(name);
        row.appendChild(del);

        container.appendChild(row);
      });
  }

  /* ================= FOLDERS ================= */

  function renderFolder(folder, container) {
    const wrapper = document.createElement("div");
    wrapper.className = "folder";

    const header = document.createElement("div");
    header.className = "folder-header";
    header.textContent = "📁 " + folder.name;

    header.onclick = () => {
      currentFolder = folder.uuid;
      markSelectedFolder(header);

      const isCollapsed = children.classList.toggle("collapsed");

      if (!isCollapsed) {
        openFolders.add(folder.uuid);
      } else {
        openFolders.delete(folder.uuid);
      }
    };


    // Drag & Drop (move files)
    header.ondragover = e => e.preventDefault();

    header.ondrop = async e => {
      e.preventDefault();
      const fileUUID = e.dataTransfer.getData("file_uuid");
      if (!fileUUID) return;

      const r = await fetch(
        `/api/projects/${PROJECT_UUID}/files/${fileUUID}/move/`,
        {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": CSRF_TOKEN
          },
          body: JSON.stringify({ folder: folder.uuid })
        }
      );

      if (r.ok) loadTree();
    };

    const del = document.createElement("button");
    del.className = "folder-delete";
    del.textContent = "🗑️";

    del.onclick = async e => {
      e.stopPropagation();

      if (!confirm(`Удалить папку "${folder.name}"?`)) return;

      const r = await fetch(
        `/api/projects/${PROJECT_UUID}/folders/${folder.uuid}/delete/`,
        {
          method: "DELETE",
          credentials: "same-origin",
          headers: { "X-CSRFToken": CSRF_TOKEN }
        }
      );

      if (r.ok) loadTree();
      else alert("Папка не пуста или нет прав");
    };

    header.appendChild(del);

    const children = document.createElement("div");
    children.className = "folder-children collapsed";

    if (openFolders.has(folder.uuid)) {
        children.classList.remove("collapsed");
    }


    renderFiles(folder.files, children);
    folder.folders.forEach(sub => renderFolder(sub, children));

    wrapper.appendChild(header);
    wrapper.appendChild(children);
    container.appendChild(wrapper);
  }

  function markSelectedFolder(header) {
    document
      .querySelectorAll(".folder-header.selected")
      .forEach(el => el.classList.remove("selected"));

    header.classList.add("selected");
  }

  /* ================= ROOT SELECT ================= */

  if (selectRoot) {
    selectRoot.onclick = () => {
      currentFolder = null;
      document
        .querySelectorAll(".folder-header.selected")
        .forEach(el => el.classList.remove("selected"));
    };
  }

  /* ================= CREATE FOLDER ================= */

  if (createRootFolderBtn) {
    createRootFolderBtn.onclick = async () => {
      const name = prompt("Название папки:");
      if (!name) return;

      const r = await fetch(`/api/projects/${PROJECT_UUID}/folders/create/`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": CSRF_TOKEN
        },
        body: JSON.stringify({
          name,
          parent: currentFolder
        })
      });

      if (!r.ok) {
        alert("Нет прав на создание папки");
        return;
      }

      loadTree();
    };
  }

  /* ================= UPLOAD ================= */

  if (dropzone && input) {
    dropzone.onclick = () => input.click();

    dropzone.ondragover = e => {
      e.preventDefault();
      dropzone.classList.add("hover");
    };

    dropzone.ondragleave = () => dropzone.classList.remove("hover");

    dropzone.ondrop = e => {
      e.preventDefault();
      dropzone.classList.remove("hover");
      uploadFiles(e.dataTransfer.files);
    };

    input.onchange = () => {
      uploadFiles(input.files);
      input.value = "";
    };
  }

  async function uploadFiles(files) {
    if (!files.length) return;

    const form = new FormData();
    [...files].forEach(f => form.append("files", f));
    if (currentFolder) {
      form.append("folder", currentFolder);
    }

    const r = await fetch(`/api/projects/${PROJECT_UUID}/files/upload/`, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": CSRF_TOKEN
      },
      body: form
    });

    if (!r.ok) {
      alert("Нет прав на загрузку файлов");
      return;
    }

    loadTree();
  }

  /* ================= INIT ================= */

  loadTree();
});
