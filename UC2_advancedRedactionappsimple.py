import tkinter as tk
from tkinter import filedialog, messagebox
import fitz
from PIL import Image, ImageTk
import io

class SecurePDFRedactorPro:

    def __init__(self, root):

        self.root = root
        self.root.title("SecurePDF Redactor Pro")
        self.root.geometry("1100x750")
        self.root.configure(bg="#20243c")

        self.doc = None
        self.page_number = 0
        self.zoom = 1.0
        self.redactions = {}

        self.start_x = None
        self.start_y = None

        self.create_ui()

    def create_ui(self):

        toolbar = tk.Frame(self.root, bg="#2c2f4a", height=50)
        toolbar.pack(fill=tk.X)

        btn_open = tk.Button(toolbar,text="Open PDF",command=self.open_pdf,bg="#4CAF50",fg="white",font=("Segoe UI",10,"bold"))
        btn_open.pack(side=tk.LEFT,padx=5,pady=10)

        btn_prev = tk.Button(toolbar,text="◀ Prev",command=self.prev_page,bg="#2196F3",fg="white")
        btn_prev.pack(side=tk.LEFT,padx=5)

        btn_next = tk.Button(toolbar,text="Next ▶",command=self.next_page,bg="#2196F3",fg="white")
        btn_next.pack(side=tk.LEFT,padx=5)

        btn_zoom_in = tk.Button(toolbar,text="Zoom +",command=self.zoom_in,bg="#9C27B0",fg="white")
        btn_zoom_in.pack(side=tk.LEFT,padx=5)

        btn_zoom_out = tk.Button(toolbar,text="Zoom -",command=self.zoom_out,bg="#9C27B0",fg="white")
        btn_zoom_out.pack(side=tk.LEFT,padx=5)

        btn_undo = tk.Button(toolbar,text="Undo",command=self.undo_redaction,bg="#FF9800",fg="white")
        btn_undo.pack(side=tk.LEFT,padx=5)

        btn_clear = tk.Button(toolbar,text="Clear Page",command=self.clear_page,bg="#FF5722",fg="white")
        btn_clear.pack(side=tk.LEFT,padx=5)

        btn_save = tk.Button(toolbar,text="Save Redacted PDF",command=self.save_pdf,bg="#E53935",fg="white",font=("Segoe UI",10,"bold"))
        btn_save.pack(side=tk.RIGHT,padx=10)

        self.page_label = tk.Label(toolbar,text="Page: 0 / 0",bg="#2c2f4a",fg="white")
        self.page_label.pack(side=tk.RIGHT,padx=10)

        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH,expand=True)

        self.canvas = tk.Canvas(frame,bg="black")
        self.canvas.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)

        scrollbar = tk.Scrollbar(frame,command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT,fill=tk.Y)

        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.bind("<ButtonPress-1>",self.start_draw)
        self.canvas.bind("<B1-Motion>",self.draw_rect)
        self.canvas.bind("<ButtonRelease-1>",self.end_draw)

    def open_pdf(self):

        path = filedialog.askopenfilename(filetypes=[("PDF Files","*.pdf")])

        if not path:
            return

        self.doc = fitz.open(path)
        self.page_number = 0
        self.zoom = 1.0
        self.redactions = {}

        self.display_page()

    def display_page(self):

        if not self.doc:
            return

        page = self.doc.load_page(self.page_number)

        mat = fitz.Matrix(self.zoom,self.zoom)
        pix = page.get_pixmap(matrix=mat)

        img_data = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(img_data))

        self.tk_img = ImageTk.PhotoImage(image)

        self.canvas.delete("all")
        self.canvas.create_image(0,0,anchor=tk.NW,image=self.tk_img)

        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        self.page_label.config(text=f"Page: {self.page_number+1} / {len(self.doc)}")

        if self.page_number in self.redactions:

            for rect in self.redactions[self.page_number]:
                self.canvas.create_rectangle(rect,fill="black")

    def prev_page(self):

        if self.doc and self.page_number > 0:
            self.page_number -= 1
            self.display_page()

    def next_page(self):

        if self.doc and self.page_number < len(self.doc)-1:
            self.page_number += 1
            self.display_page()

    def zoom_in(self):

        self.zoom += 0.2
        self.display_page()

    def zoom_out(self):

        if self.zoom > 0.4:
            self.zoom -= 0.2
            self.display_page()

    def start_draw(self,event):

        self.start_x = event.x
        self.start_y = event.y

    def draw_rect(self,event):

        self.canvas.delete("temp")

        self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            event.x,
            event.y,
            fill="black",
            width=0,
            tags="temp"
        )

    def end_draw(self,event):

        rect = (self.start_x,self.start_y,event.x,event.y)

        if self.page_number not in self.redactions:
            self.redactions[self.page_number] = []

        self.redactions[self.page_number].append(rect)

        self.display_page()

    def undo_redaction(self):

        if self.page_number in self.redactions and self.redactions[self.page_number]:
            self.redactions[self.page_number].pop()

        self.display_page()

    def clear_page(self):

        self.redactions[self.page_number] = []
        self.display_page()

    def save_pdf(self):

        if not self.doc:
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".pdf")

        if not save_path:
            return

        for page_num, rects in self.redactions.items():

            page = self.doc.load_page(page_num)

            for r in rects:

                x1,y1,x2,y2 = r

                rect = fitz.Rect(
                    x1/self.zoom,
                    y1/self.zoom,
                    x2/self.zoom,
                    y2/self.zoom
                )

                page.add_redact_annot(rect,fill=(0,0,0))

            page.apply_redactions()

        self.doc.save(save_path)

        messagebox.showinfo("Success","PDF saved with permanent redactions.")

if __name__ == "__main__":

    root = tk.Tk()
    app = SecurePDFRedactorPro(root)
    root.mainloop()
