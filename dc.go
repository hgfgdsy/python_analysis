package main

import (
	"C"
	"encoding/json"
	"net/url"
	"path"
	"regexp"
	"strings"
)


//export DecodeSource
func DecodeSource(Csource *C.char) *C.char {
	source := C.GoString(Csource)
	var u *url.URL
	var p string
	rg := regexp.MustCompile("^([a-zA-Z0-9_]+)@([a-zA-Z0-9._-]+):(.*)$")
	if m := rg.FindStringSubmatch(source); m != nil {
		// Match SCP-like syntax and convert it to a URL.
		// Eg, "git@github.com:user/repo" becomes
		// "ssh://git@github.com/user/repo".
		u = &url.URL{
			Scheme: "ssh",
			User:   url.User(m[1]),
			Host:   m[2],
			Path:   "/" + m[3],
		}
	} else {
		var err error
		u, err = url.Parse(source)
		if err != nil {
			p = "wrong"
			return C.CString(p)
		}
	}
	// If no scheme was passed, then the entire path will have been put into
	// u.Path. Either way, construct the normalized path correctly.
	if u.Host == "" {
		p = source
	} else {
		p = path.Join(u.Host, u.Path)
	}
	p = strings.TrimSuffix(p, ".git")
	p = strings.TrimSuffix(p, ".hg")
	return C.CString(p)
}


//export Sum
func Sum(a int, b int) int{
	return a+b
}


//export Godepssup
func Godepssup(Cdata *C.char) *C.char{
	CSdata := C.GoString(Cdata)
	var data []byte = []byte(CSdata)
	var cfg struct {
		ImportPath string
		Deps       []struct {
			ImportPath string
			Rev        string
		}
	}
	var p string
	if err := json.Unmarshal(data, &cfg); err != nil {
		p = ""
		return C.CString(p)
	}
	p = ""
	for _, d := range cfg.Deps {
		p = p + d.ImportPath + "\t" + d.Rev + "\n"
	}
	return C.CString(p)
}


//export Vjsonsup
func Vjsonsup(Cdata *C.char) *C.char{
	CSdata := C.GoString(Cdata)
	var data []byte = []byte(CSdata)
	var cfg struct {
		Package []struct {
			Path     string
			Revision string
		}
	}
	var p string
	if err := json.Unmarshal(data, &cfg); err != nil {
		p = ""
		return C.CString(p)
	}
	p = ""
	for _, d := range cfg.Package {
		p = p + d.Path + "\t" + d.Revision + "\n"
	}
	return C.CString(p)
}


//export Vmanisup
func Vmanisup(Cdata *C.char) *C.char{
	CSdata := C.GoString(Cdata)
	var data []byte = []byte(CSdata)
	var cfg struct {
		Dependencies []struct {
			ImportPath string
			Revision   string
		}
	}
	var p string
	if err := json.Unmarshal(data, &cfg); err != nil {
		p = ""
		return C.CString(p)
	}
	p = ""
	for _, d := range cfg.Dependencies {
		p = p + d.ImportPath + "\t" + d.Revision + "\n"
	}
	return C.CString(p)
}


func main(){}
