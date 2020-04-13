Translates JavaScript to Python code. Js2Py is able to translate and execute virtually any JavaScript code.

Js2Py is written in pure python and does not have any dependencies. Basically an implementation of JavaScript core in pure python.


    import js2py

    f = js2py.eval_js( "function (name) {return name.length}" )

    f("Piotr")

    # returns 5


More examples at: https://github.com/PiotrDabkowski/Js2Py


