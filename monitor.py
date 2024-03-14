import os, subprocess, enum, threading, time

class Config:
    interface           : str;
    max_pps             : int = 7500;
    max_connections     : int = 20;
    cons_per_port       : int = 5;
    protected_ips       : list[str] = [];
    protected_ports     : list[str] = [];

class State_T(enum.Enum):
    _null			    = 0x10001;
    close_wait		    = 0x10002;
    closed			    = 0x10003;
    established		    = 0x10004;
    fin_wait1		    = 0x10005;
    fin_wait2 		    = 0x10006;
    last_ack		    = 0x10007;
    listen			    = 0x10008;
    syn_recv		    = 0x10009;
    syn_sent		    = 0x10010;
    time_wait		    = 0x10011;
    closing			    = 0x10012;

class Nload():
    curr 		        : str;
    avg			        : str;
    min 		        : str;
    max 		        : str;
    ttl 		        : str;
    def __init__(self) -> None:
        self.curr = ""; self.avg = ""; self.min = "";
        self.max = ""; self.ttl = "";

class Con():
    protocol		    : str;
    recv_bytes		    : int;
    sent_bytes		    : int;
    internal_ip 	    : str;
    internal_port	    : int;
    external_ip		    : str;
    external_port	    : int;
    state			    : State_T;

    def __init__(self, arr: list[str]):
        self.protocol           = arr[0];
        self.recv_bytes         = arr[1];
        self.sent_bytes         = arr[2];
        self.internal_ip        = arr[3];
        self.internal_port      = arr[4];
        self.external_ip        = arr[5];
        self.external_port      = arr[6];
        self.state              = Con.state2type(arr[7]);
    
    def isAlive(self) -> bool:
        if self.state in [
            State_T.established, 
            State_T.syn_recv,
            State_T.time_wait,
            State_T.close_wait,
            State_T.last_ack
        ]:
            return True;
        return False;

    def isRecvHigh(self) -> bool:
        if self.recv_bytes > 50: return True;
        return False;

    @staticmethod
    def state2type(st: str) -> State_T:
        if st == "close_wait": return State_T.close_wait;
        elif st == "closed": return State_T.closed;
        elif st == "established": return State_T.established;
        elif st == "fin_wait1": return State_T.fin_wait1;
        elif st == "fin_wait2": return State_T.fin_wait2;
        elif st == "last_ack": return State_T.last_ack;
        elif st == "listen": return State_T.listen;
        elif st == "syn_recv": return State_T.syn_recv;
        elif st == "syn_sent": return State_T.syn_sent;
        elif st == "time_wait": return State_T.time_wait;
        elif st == "closing": return State_T.closing;
        return "";
    

class Utils:
    """ Color """
    c_default 		: str = "\x1b[39m";
    c_black 		: str = "\x1b[30m";
    c_red			: str = "\x1b[31m";
    c_green 		: str = "\x1b[32m";
    c_yellow		: str = "\x1b[33m";
    c_blue			: str = "\x1b[34m";
    c_magenta		: str = "\x1b[35m";
    c_cyan			: str = "\x1b[36m";
    c_lightgray		: str = "\x1b[37m";
    c_darkgray		: str = "\x1b[90m";
    c_lightred		: str = "\x1b[91m";
    c_lightgreen	: str = "\x1b[92m";
    c_lightyellow	: str = "\x1b[93m";
    c_lightblue		: str = "\x1b[94m";
    c_lightmagenta	: str = "\x1b[95m";
    c_lightcyan		: str = "\x1b[96m";
    c_white			: str = "\x1b[97m";

    """ Background Colors """
    bg_default		: str = "\x1b[49m";
    bg_black		: str = "\x1b[40m";
    bg_red			: str = "\x1b[41m";
    bg_green		: str = "\x1b[42m";
    bg_yellow		: str = "\x1b[43m";
    bg_blue			: str = "\x1b[44m";
    bg_magenta		: str = "\x1b[45m";
    bg_cyan			: str = "\x1b[46m";
    bg_lightgray	: str = "\x1b[47m";
    bg_darkgray		: str = "\x1b[100m";
    bg_lightred		: str = "\x1b[101m";
    bg_lightgreen	: str = "\x1b[102m";
    bg_lightyellow	: str = "\x1b[103m";
    bg_lightblue	: str = "\x1b[104m";
    bg_lightmagenta : str = "\x1b[105m";
    bg_lightcyan	: str = "\x1b[106m";
    bg_white 		: str = "\x1b[107m";

    clear		 	: str = "\033[2J\033[1;1H"

    colors 			: dict[str, str] = {
		"{DEFAULT}": 			c_default,
		"{BLACK}": 				c_black,
		"{RED}": 				c_red,
		"{GREEN}": 				c_green,
		"{YELLOW}": 			c_yellow,
		"{BLUE}": 				c_blue,
		"{MAGENTA}": 			c_magenta,
		"{CYAN}": 				c_cyan,
		"{LIGHTGRAY}": 			c_lightgray,
		"{DARKGRAY}": 			c_darkgray,
		"{LIGHTRED}": 			c_lightred,
		"{LIGHTGREEN}": 		c_lightgreen,
		"{LIGHTYELLOW}": 		c_lightyellow,
		"{LIGHTBLUE}": 			c_lightblue,
		"{LIGHTMAGENTA}": 		c_lightmagenta,
		"{LIGHTCYAN}": 			c_lightcyan,
		"{WHITE}": 				c_white,
		"{BG_DEFAULT}":			bg_default,
		"{BG_BLACK}":			bg_black,
		"{BG_RED}":				bg_red,
		"{BG_GREEN}":			bg_green,
		"{BG_YELLOW}":			bg_yellow,
		"{BG_BLUE}":			bg_blue,
		"{BG_MAGENTA}":			bg_magenta,
		"{BG_CYAN}":			bg_cyan,
		"{BG_LIGHTGRAY}":		bg_lightgray,
		"{BG_DARKGRAY}":		bg_darkgray,
		"{BG_LIGHTRED}":		bg_lightred,
		"{BG_LIGHTGREEN}":		bg_lightgreen,
		"{BG_LIGHTYELLOW}":		bg_lightyellow,
		"{BG_LIGHTBLUE}":		bg_lightblue,
		"{BG_LIGHTMAGENTA}":	bg_lightmagenta,
		"{BG_LIGHTCYAN}":		bg_lightcyan,
		"{BG_WHITE}":			bg_white
	}
    @staticmethod
    def rm_empty_elements(arr: list[str]) -> list[str]:
        new = [];

        for element in arr:
            if element != "": new.append(element);

        return new;

    @staticmethod
    def set_title(t: str) -> None:
        print(f"\033]0;{t}\007", end="");

    @staticmethod
    def set_term_size(r: int, c: int) -> None:
        print(f"\033[8;{r};{c}t", end="");

    @staticmethod
    def place_text(r: int, c: int, t: str) -> None:
        print(f"\033[{r};{c}f${t}", end="");

    @staticmethod
    def list_text(r: int, c: int, t: str) -> None:
        row = r;

        for line in t.split("\n"):
            print(f"\x1b[{row};{c}f{line}", end="");
            time.sleep(.75);
            row+=1;

    @staticmethod
    def replace_colors(data: str) -> str:
        new = data;

        for name in Utils.colors:
            ansi = Utils.colors[name];
            new = new.replace(name, ansi);

        return new;

class SystemInformation:

    @staticmethod
    def get_nload(interface: str) -> Nload:
        nload = Nload();
        subprocess.getoutput(f"timeout 1 nload {interface} -m -u g > t.txt");

        fd = open("t.txt", "r");
        data = fd.read();
        lines = data.split("\n");

        for line in lines:
            if "Curr:" in line: nload.curr = line.split(" ")[1].strip();
            elif "Avg:" in line: nload.avg = line.split(" ")[1].strip();
            elif "Min:" in line: nload.min = line.split(" ")[1].strip();
            elif "Max:" in line: nload.max = line.split(" ")[1].strip();
            elif "Ttl:" in line: nload.ttl = line.split(" ")[1].strip();

        fd.close();
        return nload;


    @staticmethod
    def fetch_cons() -> list[Con]:
        cons = list[Con]
        data = subprocess.getoutput("netstat -tn");
        lines = data.split("\n");

        for line in lines:
            line_info = line.split(" ");
            ip_info = Utils.rm_empty_elements(line_info);
            
            if len(ip_info) < 4 or ":" not in line: continue;
            cons.append(Con(ip_info));
    
        return cons;

"""
    - Main Entry
"""
class Main():
    """ Retrieve Information Upon Start-up """
    interface   : str;
    system_ip	: str;
    upload		: str;
    download	: str;
    ms			: str;

    """ Run-time updating objects """
    cons        : list[Con];
    pps         : int;
    nload       : Nload;

    """ Configuration Settings ( Must be set before starting up! ) """
    cfg         : Config;
    def __init__(self, c: Config) -> None:
        print("[ + ] Starting CyberShield.....");
        self.retrieve_cfg();
        self.nload = Nload();
        self.cfg = c;
        self.fetch_interface();
        print("[ + ] Grabbing Connection Information....");
        self.get_connection_speed();
        self.get_speed_ms();

        print("[ + ] Starting Monitor.....");
        self.start_monitor();

    def retrieve_cfg(self) -> None:
        if not os.path.exists("layout.txt"):
            return;
        
        layout_fd = open("layout.txt", "r")
        self.layout = layout_fd.read();
        layout_fd.close();
    
        if not os.path.exists("graph.txt"):
            return;
        
        graph_fd = open("graph.txt", "r");
        self.graph = graph_fd.read();
        graph_fd.close();
    
    def fetch_interface(self) -> None:
        ifconfig_lines = subprocess.getoutput("ifconfig").split("\n");

        interfaces = [];
        interface_ips = [];

        i = 0
        for line in ifconfig_lines:
            if len(line) < 3: continue;
            line_data = Utils.rm_empty_elements(line.split(" "));
            if line_data[0].endswith(":"):
                interfaces.append(line_data[0]);
                interface_ips.append(Utils.rm_empty_elements(ifconfig_lines[i+1].strip().split(" "))[1]);
            i+=1

        if self.cfg.interface == "" or self.cfg.interface not in interfaces:
            ask_for_interface = input(f"Which interface do you want to use? (1-{len(interfaces)})\r\n\t=> {interfaces}: ");
            if not isinstance(ask_for_interface, int) and not ask_for_interface.isdigit():
                return
            
            self.interface = interfaces[int(ask_for_interface)].replace(":", "");
            self.system_ip = interface_ips[int(ask_for_interface)];
    
        c = 0
        for iface in interfaces:
            if iface == self.cfg.interface:
                self.system_ip = interface_ips[c];
            c+=1


    def start_monitor(self) -> None:        
        while True:
            threading.Thread(target=SystemInformation.get_nload, args=(self.interface,)).start();
            if self.nload.curr:
                print(f"{self.nload.curr}", end="");
                print(f"{self.nload.avg}", end="");
                print(f"{self.nload.min}", end="");
                print(f"{self.nload.max}", end="");
                print(f"{self.nload.ttl}", end="");
    
    def get_speed_ms(self) -> None:
        lines = subprocess.getoutput("timeout 1 ping 1.1.1.1").split(" ");
        
        if len(lines) > 0:
            self.ms = lines[1].split(" ")[len(lines[1].split(" "))-2].replace("time=", "")


    def get_connection_speed(self) -> None:
        print(f"[ + ] Monitoring {self.interface} | {self.system_ip}....!")
        lines = subprocess.getoutput("/usr/bin/speedtest")

        for line in lines:
            if line.strip().startswith("Download:"):
                self.download = line.strip().replace("Download:", "").strip();
            elif line.strip().startswith("Upload:"):
                self.upload = line.strip().replace("Upload:", "").strip();

cfg = Config()
cfg.interface = "";
Main(cfg);