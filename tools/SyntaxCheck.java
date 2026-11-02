import com.sun.source.util.JavacTask;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;

/**
 * Parse-only check of all .java files under a directory (syntax errors only, no symbol resolution).
 * Usage: java tools/SyntaxCheck.java src/main/java
 * It exists because the real compilation needs the Forge toolchain; it does NOT replace gradlew build.
 */
public class SyntaxCheck {
    public static void main(String[] args) throws IOException {
        Path root = Path.of(args.length > 0 ? args[0] : "src/main/java");
        List<Path> files = new ArrayList<>();
        try (Stream<Path> walk = Files.walk(root)) {
            walk.filter(p -> p.toString().endsWith(".java")).forEach(files::add);
        }
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        try (StandardJavaFileManager fm = compiler.getStandardFileManager(diagnostics, null, null)) {
            JavacTask task = (JavacTask) compiler.getTask(null, fm, diagnostics, List.of("-proc:none"), null,
                    fm.getJavaFileObjectsFromPaths(files));
            task.parse();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        int errors = 0;
        for (Diagnostic<? extends JavaFileObject> d : diagnostics.getDiagnostics()) {
            if (d.getKind() == Diagnostic.Kind.ERROR) {
                errors++;
                System.out.println("SYNTAX ERROR " + d.getSource().getName() + ":" + d.getLineNumber() + ": "
                        + d.getMessage(null));
            }
        }
        System.out.println(files.size() + " files parsed, " + errors + " syntax error(s)");
        System.exit(errors == 0 ? 0 : 1);
    }
}
